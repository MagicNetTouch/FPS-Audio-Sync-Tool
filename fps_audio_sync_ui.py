import os, sys, json, threading, subprocess, re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES # type: ignore

# ================= CONFIG =================
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_BITRATE = "192k"

# ================= FFMPEG PATH =================
def tool_path(name):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, name) # type: ignore
    return name

FFMPEG = tool_path("ffmpeg.exe")
FFPROBE = tool_path("ffprobe.exe")

# ================= LOGGING =================
def log(msg):
    log_box.config(state="normal")
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    root.update_idletasks()
    log_box.config(state="disabled")

# ================= HELPERS =================
def format_duration(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}"

def get_fps(video_path):
    cmd = [FFPROBE, "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=r_frame_rate", "-of", "json", video_path]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    rate = json.loads(r.stdout)["streams"][0]["r_frame_rate"]
    num, den = map(int, rate.split("/"))
    return num / den

def get_duration(video_path):
    cmd = [FFPROBE, "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

def get_video_codec(video_path):
    cmd = [
        FFPROBE,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,codec_long_name",
        "-of",
        "json",
        video_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    streams = data.get("streams") or []
    if not streams:
        return ""
    stream = streams[0]
    short_name = stream.get("codec_name") or ""
    long_name = stream.get("codec_long_name") or ""
    if long_name and short_name:
        return f"{long_name} ({short_name})"
    if long_name:
        return long_name
    return short_name

def parse_language_selection(label):
    cleaned = label.replace("(", " ").replace(")", " ").replace(",", " ")
    tokens = cleaned.split()
    code = ""
    for t in tokens:
        if t.isalpha() and 2 <= len(t) <= 3:
            code = t.lower()
            break
    name = label.split("(")[0].strip() or label.strip()
    return name, code

def get_audio_stream_count(video_path):
    cmd = [
        FFPROBE, "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index",
        "-of", "json",
        video_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    return len(data.get("streams", []))

def update_progress(val, text):
    progress_var.set(val)
    status_var.set(f"{text}: {val:.1f}%")

def run_ffmpeg_with_progress(cmd, total_duration, description):
    log(f"{description}...")
    root.after(0, lambda: update_progress(0, description))

    startupinfo = None
    if os.name == 'nt':
        try:
            startupinfo = subprocess.STARTUPINFO() # type: ignore
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW # type: ignore
            startupinfo.wShowWindow = subprocess.SW_HIDE # type: ignore
        except AttributeError:
            pass

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        startupinfo=startupinfo,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace'
    )

    if process.stderr is None:
        raise RuntimeError(f"Failed to open stderr for {description}")
    
    stderr_pipe = process.stderr

    # Use deque to keep only recent lines and avoid slicing issues
    from collections import deque
    stderr_lines = deque(maxlen=20)
    pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")

    while True:
        line = stderr_pipe.readline() # type: ignore
        if not line and process.poll() is not None:
            break
        if line:
            stderr_lines.append(line)
            match = pattern.search(line)
            if match and total_duration > 0:
                h, m, s, ms = map(int, match.groups())
                current = h * 3600 + m * 60 + s + ms / 100.0
                percent = min(100, (current / total_duration) * 100)
                root.after(0, lambda p=percent, d=description: update_progress(p, d))

    if process.returncode != 0:
        err_msg = "".join(stderr_lines)
        raise Exception(f"FFmpeg Error in {description}:\n{err_msg}")

    root.after(0, lambda: update_progress(100, "Done"))

# ================= AUDIO PROCESS =================
def process_audio(src_video, tgt_video, audio_format, bitrate, sample_rate,
                  lang, mux_video, delay_ms, stretch_duration, fast_mode, set_default_track=False):

    log("Analyzing FPS and duration…")
    fps_src = get_fps(src_video)
    fps_tgt = get_fps(tgt_video)
    duration_src = get_duration(src_video)
    duration_tgt = get_duration(tgt_video)

    log(f"Source FPS: {fps_src:.6f}, Target FPS: {fps_tgt:.6f}")
    log(f"Source duration: {format_duration(duration_src)}, Target duration: {format_duration(duration_tgt)}")

    # Determine stretch ratio
    if stretch_duration:
        stretch_ratio = duration_src / duration_tgt
        log(f"Stretching audio based on duration ratio: {stretch_ratio:.8f}")
    else:
        stretch_ratio = fps_tgt / fps_src
        log(f"Stretching audio based on FPS ratio: {stretch_ratio:.8f}")

    # Apply delay
    scaled_delay_ms = int(delay_ms)
    log(f"Applying delay: {scaled_delay_ms} ms")

    # Build filter complex
    filters = []
    
    # 1. Stretching
    if fast_mode:
        # Fast mode: Use asetrate (resampling) which changes pitch
        # Logic: Play at (sample_rate * ratio), then resample back to sample_rate
        new_rate = int(sample_rate * stretch_ratio)
        log(f"Fast Mode (Pitch Shift): Setting input rate to {new_rate}Hz, then resampling to {sample_rate}Hz")
        filters.append(f"asetrate={new_rate}")
        filters.append(f"aresample={sample_rate}")
    else:
        # Normal mode: Use atempo (time-stretch, pitch preserved)
        # atempo filter is limited to [0.5, 2.0], so we chain if needed
        frames_ratio = stretch_ratio
        while frames_ratio > 2.0:
            filters.append("atempo=2.0")
            frames_ratio /= 2.0
        while frames_ratio < 0.5:
            filters.append("atempo=0.5")
            frames_ratio /= 0.5
        
        if abs(frames_ratio - 1.0) > 1e-6:
            filters.append(f"atempo={frames_ratio:.8f}")

    # 2. Delay (adelay) or Trim (atrim)
    if scaled_delay_ms > 0:
        # positive delay: insert silence at start
        # adelay syntax: delays in ms. 'all=1' applies to all channels
        filters.append(f"adelay={scaled_delay_ms}:all=1")
    elif scaled_delay_ms < 0:
        # negative delay: trim start
        trim_sec = abs(scaled_delay_ms) / 1000.0
        filters.append(f"atrim=start={trim_sec}")
        filters.append("asetpts=PTS-STARTPTS")

    # Construct filter string
    filter_str = ",".join(filters) if filters else "anull"
    
    log(f"Generated FFmpeg Filter Complex: {filter_str}")

    base = os.path.splitext(os.path.basename(src_video))[0]
    ext = "mp3" if audio_format == "mp3" else "aac"
    final_audio = os.path.join(os.path.dirname(src_video), f"{base}_audio.{ext}")
    
    # Determine encoder
    codec = "libmp3lame" if audio_format == "mp3" else "aac"

    # Step 1: Single Pass Encoding
    total_steps = 2 if mux_video else 1
    current_step = 1

    cmd = [
        FFMPEG, "-y",
        "-i", src_video,
        "-vn", # No video
        "-filter:a", filter_str,
        "-c:a", codec,
        "-b:a", bitrate,
        "-ar", str(sample_rate),
        "-threads", "0",          # Enable multi-threading for encoding
        "-filter_threads", "8",   # Enable multi-threading for filters
        "-filter_complex_threads", "8", # Enable multi-threading for complex filters
        final_audio
    ]

    log("Starting single-pass audio encoding (Extract + Stretch + Delay + Encode)...")
    
    # Estimate output duration for progress
    expected_duration = duration_tgt
    if scaled_delay_ms < 0:
        expected_duration = max(0.0, duration_tgt - (abs(scaled_delay_ms)/1000.0))
    elif scaled_delay_ms > 0:
        expected_duration = duration_tgt + (scaled_delay_ms/1000.0)

    run_ffmpeg_with_progress(cmd, expected_duration, f"Step {current_step}/{total_steps}: Encoding Audio")
    
    log(f"Audio processed: {final_audio}")

    # Step 2: Mux (optional)
    out_video = None
    if mux_video:
        current_step += 1
        ext = os.path.splitext(tgt_video)[1]
        out_video = os.path.join(
            os.path.dirname(tgt_video),
            f"{os.path.splitext(os.path.basename(tgt_video))[0]}_audio_{lang}{ext}"
        )

        # Count existing audio streams
        existing_audio_count = get_audio_stream_count(tgt_video)
        new_audio_index = existing_audio_count  # NEW audio goes last

        lang_name, lang_code = parse_language_selection(lang)
        if not lang_code:
            lang_code = "und"

        log(f"Muxing audio into target video as language={lang_name} ({lang_code}) (original audio untouched)…")

        cmd_mux = [
            FFMPEG, "-y",
            "-i", tgt_video,
            "-i", final_audio,

            "-map", "0:v",
            "-map", "0:a?",
            "-map", "1:a",

            "-c:v", "copy",
            "-c:a", "copy",

            f"-metadata:s:a:{new_audio_index}", f"language={lang_code}",
            f"-metadata:s:a:{new_audio_index}", f"title={lang_name}",

            out_video
        ]

        if set_default_track:
            log("Setting new audio track as DEFAULT")
            for i in range(existing_audio_count):
                cmd_mux.insert(-1, f"-disposition:a:{i}")
                cmd_mux.insert(-1, "0")
            
            cmd_mux.insert(-1, f"-disposition:a:{new_audio_index}")
            cmd_mux.insert(-1, "default")

        run_ffmpeg_with_progress(cmd_mux, duration_tgt, f"Step {current_step}/{total_steps}: Muxing video")
        log(f"Output video with added audio: {out_video}")

    return final_audio, out_video

# ================= UI LOGIC =================
def start_processing():
    if not vid1_var.get() or not vid2_var.get():
        messagebox.showerror("Error", "Please select source and target video files.")
        return

    log_box.config(state="normal")
    log_box.delete("1.0", tk.END)
    log_box.config(state="disabled")
    btn.config(state="disabled")

    audio_format = audio_format_var.get()
    bitrate = bitrate_var.get()
    sample_rate = int(sample_rate_var.get())
    lang = lang_var.get()
    mux_video = mux_var.get()
    delay_ms = int(audio_delay_var.get())
    stretch_duration = stretch_duration_var.get()
    fast_mode = fast_mode_var.get()
    set_default = set_default_var.get()

    def worker():
        try:
            out_audio, out_video = process_audio(
                vid1_var.get(), vid2_var.get(),
                audio_format, bitrate, sample_rate, lang, mux_video,
                delay_ms, stretch_duration, fast_mode, set_default
            )
            messagebox.showinfo("Done",
                                f"Audio created:\n{out_audio}" +
                                (f"\n\nVideo with audio:\n{out_video}" if out_video else ""))
        except Exception as e:
            messagebox.showerror("Error", str(e))
            log(f"ERROR: {e}")
        finally:
            btn.config(state="normal")

    threading.Thread(target=worker, daemon=True).start()

def on_drop(event):
    files = root.tk.splitlist(event.data)
    for f in files:
        fps = get_fps(f)
        duration = get_duration(f)
        codec = get_video_codec(f)
        if not vid1_var.get():
            vid1_var.set(f)
            log(
                f"Loaded Source Video File: {os.path.basename(f)} / FPS: {fps:.6f} / Duration: {format_duration(duration)} / Codec: {codec}"
            )
        elif not vid2_var.get():
            vid2_var.set(f)
            log(
                f"Loaded Target Video File: {os.path.basename(f)} / FPS: {fps:.6f} / Duration: {format_duration(duration)} / Codec: {codec}"
            )

def browse_source():
    file = filedialog.askopenfilename(title="Select Source Video File",
                                      filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi *.flv *.webm")])
    if file:
        vid1_var.set(file)
        fps = get_fps(file)
        duration = get_duration(file)
        codec = get_video_codec(file)
        log(
            f"Loaded Source Video File: {os.path.basename(file)} / FPS: {fps:.6f} / Duration: {format_duration(duration)} / Codec: {codec}"
        )

def browse_target():
    file = filedialog.askopenfilename(title="Select Target Video File",
                                      filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi *.flv *.webm")])
    if file:
        vid2_var.set(file)
        fps = get_fps(file)
        duration = get_duration(file)
        codec = get_video_codec(file)
        log(
            f"Loaded Target Video File: {os.path.basename(file)} / FPS: {fps:.6f} / Duration: {format_duration(duration)} / Codec: {codec}"
        )

# ================= UI =================
root = TkinterDnD.Tk()
root.title("FPS Audio Sync Tool by Gant")

# Configure columns
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=0)
root.rowconfigure(11, weight=1)

vid1_var = tk.StringVar()
vid2_var = tk.StringVar()
audio_format_var = tk.StringVar(value="aac")
bitrate_var = tk.StringVar(value=DEFAULT_BITRATE)
sample_rate_var = tk.StringVar(value=str(DEFAULT_SAMPLE_RATE))
lang_var = tk.StringVar(value="Greek (modern, 1453-) (el, gre)")
mux_var = tk.BooleanVar(value=True)
audio_delay_var = tk.StringVar(value="0")
stretch_duration_var = tk.BooleanVar(value=False)
set_default_var = tk.BooleanVar(value=False)
status_var = tk.StringVar(value="Ready")
progress_var = tk.DoubleVar(value=0)

# Source video row with frame
tk.Label(root, text="Source Video File").grid(row=0, column=0, sticky="w", padx=5, pady=2)
source_frame = tk.Frame(root)
source_frame.grid(row=0, column=1, columnspan=2, sticky="ew", padx=2)
source_frame.columnconfigure(0, weight=1)
tk.Entry(source_frame, textvariable=vid1_var).grid(row=0, column=0, sticky="ew")
tk.Button(source_frame, text="Browse", command=browse_source, width=12).grid(row=0, column=1, sticky="e", padx=5)

# Target video row with frame
tk.Label(root, text="Target Video File").grid(row=1, column=0, sticky="w", padx=5, pady=2)
target_frame = tk.Frame(root)
target_frame.grid(row=1, column=1, columnspan=2, sticky="ew", padx=2)
target_frame.columnconfigure(0, weight=1)
tk.Entry(target_frame, textvariable=vid2_var).grid(row=0, column=0, sticky="ew")
tk.Button(target_frame, text="Browse", command=browse_target, width=12).grid(row=0, column=1, sticky="e", padx=5)

# Audio options
tk.Label(root, text="Audio Format").grid(row=2, column=0, sticky="w", padx=5, pady=2)
ttk.Combobox(root, textvariable=audio_format_var, values=["mp3", "aac"], state="readonly").grid(row=2, column=1, sticky="w", padx=2)

tk.Label(root, text="Bitrate").grid(row=3, column=0, sticky="w", padx=5, pady=2)
ttk.Combobox(root, textvariable=bitrate_var, values=["128k","192k","256k","320k"], state="readonly").grid(row=3, column=1, sticky="w", padx=2)

tk.Label(root, text="Sample Rate (Hz)").grid(row=4, column=0, sticky="w", padx=5, pady=2)
ttk.Combobox(root, textvariable=sample_rate_var, values=["44100","48000"], state="readonly").grid(row=4, column=1, sticky="w", padx=2)

# Audio language
tk.Label(root, text="Audio Language").grid(row=5, column=0, sticky="w", padx=5, pady=2)
languages = [
    "English (en)", "Greek (modern, 1453-) (el, gre)", "Spanish (es)", "French (fr)",
    "German (de)", "Italian (it)", "Japanese (ja)", "Chinese (zh)", "Russian (ru)"
]
ttk.Combobox(root, textvariable=lang_var, values=languages, state="readonly").grid(row=5, column=1, sticky="w", padx=2)

# Mux options frame
mux_frame = tk.Frame(root)
mux_frame.grid(row=5, column=2, sticky="e", padx=5)
tk.Checkbutton(mux_frame, text="Mux audio", variable=mux_var).pack(side="left")
tk.Checkbutton(mux_frame, text="Set as Default", variable=set_default_var).pack(side="left", padx=5)

# Audio delay input
tk.Label(root, text="Audio Delay (ms)").grid(row=6, column=0, sticky="w", padx=5, pady=2)
tk.Entry(root, textvariable=audio_delay_var).grid(row=6, column=1, sticky="w", padx=2)

# Stretch options frame
stretch_frame = tk.Frame(root)
stretch_frame.grid(row=6, column=2, sticky="w", padx=5)

# Stretch duration checkbox
tk.Checkbutton(stretch_frame, text="Stretch to exact duration",
               variable=stretch_duration_var).pack(side="left")

# Fast mode checkbox
fast_mode_var = tk.BooleanVar(value=False)
tk.Checkbutton(stretch_frame, text="Fast Mode (Pitch Shift)",
               variable=fast_mode_var).pack(side="left", padx=5)

# Drag & drop area
drop = tk.Label(root, text="Drag & drop two videos here", relief="groove", height=3)
drop.grid(row=7, column=0, columnspan=3, sticky="ew", padx=5, pady=4)
drop.drop_target_register(DND_FILES) # type: ignore
drop.dnd_bind("<<Drop>>", on_drop) # type: ignore

# Start button
btn = ttk.Button(root, text="Start Processing", command=start_processing)
btn.grid(row=8, column=0, columnspan=3, pady=6, sticky="ew", padx=5)

# Status and Progress
tk.Label(root, textvariable=status_var).grid(row=9, column=0, columnspan=3, sticky="w", padx=5)
ttk.Progressbar(root, variable=progress_var, maximum=100).grid(row=10, column=0, columnspan=3, sticky="ew", padx=5, pady=2)

# Log panel
log_box = tk.Text(root, height=14)
log_box.grid(row=11, column=0, columnspan=3, sticky="nsew", padx=5, pady=4)
log_box.config(state="disabled")

root.mainloop()
