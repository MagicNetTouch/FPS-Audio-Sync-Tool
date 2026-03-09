import os, sys, json, threading, subprocess, re, time
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
           "-show_entries", "stream=r_frame_rate,avg_frame_rate", "-of", "json", video_path]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)["streams"][0]
    
    r_rate = data.get("r_frame_rate", "0/0")
    avg_rate = data.get("avg_frame_rate", "0/0")
    
    def parse_rate(rate_str):
        try:
            num, den = map(int, rate_str.split("/"))
            return num / den if den != 0 else 0
        except:
            return 0
            
    fps_r = parse_rate(r_rate)
    fps_avg = parse_rate(avg_rate)
    
    log(f"FPS Detection - r_frame_rate: {r_rate} ({fps_r:.4f}), avg_frame_rate: {avg_rate} ({fps_avg:.4f})")
    
    if fps_avg > 0:
        return fps_avg
    return fps_r

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

def get_audio_tracks_info(video_path):
    cmd = [
        FFPROBE, "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index,codec_name:stream_tags", # Get all tags
        "-of", "json",
        video_path
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(r.stdout)
        streams = data.get("streams", [])
        tracks = []
        for i, s in enumerate(streams):
            codec = s.get("codec_name", "unknown")
            tags = s.get("tags", {})
            
            # Log tags for debugging
            try:
                # Format tags for nicer output
                tag_str = ", ".join([f"{k}={v}" for k, v in tags.items()])
                log(f"Track {i+1} tags: {tag_str}")
            except:
                pass

            # Try to find language (case-insensitive)
            lang = ""
            for k, v in tags.items():
                if k.lower() == "language":
                    lang = v
                    break
            
            # If lang is empty or und, try checking handler_name
            if not lang or lang == "und":
                 handler = ""
                 for k, v in tags.items():
                     if k.lower() == "handler_name":
                         handler = v
                         break
                 
                 # Basic heuristic: if handler looks like a lang code
                 if handler and len(handler) <= 3 and handler.isalpha():
                     lang = handler
            
            # Fallback: Check filename for language if still unknown
            if not lang or lang == "und":
                try:
                    filename = os.path.basename(video_path)
                    # Check for pattern "_audio_CODE." or "(CODE)"
                    # Regex for common language codes in brackets or after _audio_
                    # e.g. "video_audio_Greek (modern, 1453-) (el, gre).mp4" -> matches "el"
                    # e.g. "video_audio_el.mp4" -> matches "el"
                    
                    # Look for (code) pattern
                    matches = re.findall(r'\((\w{2,3})\)', filename)
                    if matches:
                        # Take the last one as it's often the language
                        lang = matches[-1]
                    
                    # Look for _audio_code pattern
                    if not lang or lang == "und":
                         match = re.search(r'_audio_([a-z]{2,3})\.', filename)
                         if match:
                             lang = match.group(1)
                except:
                    pass

            if not lang:
                lang = "und"

            # Try to find title (case-insensitive)
            title = ""
            for k, v in tags.items():
                if k.lower() == "title":
                    title = v
                    break

            label = f"Track {i+1}: {codec} [{lang}]"
            if title:
                label += f" - {title}"
            tracks.append(label)
        return tracks
    except Exception as e:
        print(f"Error getting audio tracks: {e}")
        try:
            log(f"Error getting audio tracks: {e}")
        except:
            pass
        return ["Track 1: Default"]

def parse_language_selection(label):
    cleaned = label.replace("(", " ").replace(")", " ").replace(",", " ")
    tokens = cleaned.split()
    code = ""
    # Prefer 3-letter codes (ISO 639-2)
    for t in tokens:
        if t.isalpha() and len(t) == 3:
            code = t.lower()
            break
    # Fallback to 2-letter codes (ISO 639-1)
    if not code:
        for t in tokens:
            if t.isalpha() and len(t) == 2:
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

def update_progress(val, text, extra=""):
    progress_var.set(val)
    status_var.set(f"{text}: {val:.1f}% {extra}".strip())

cancel_event = threading.Event()

def run_ffmpeg_with_progress(cmd, total_duration, description):
    log(f"{description}...")
    root.after(0, lambda: update_progress(0, description))

    start_time = time.time()

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
        if cancel_event.is_set():
            process.terminate()
            raise Exception("Process stopped by user")

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
                
                elapsed = time.time() - start_time
                if percent > 0:
                    remaining = elapsed * ((100 - percent) / percent)
                    extra = f"- Elapsed: {format_duration(elapsed)} Remaining: {format_duration(remaining)}"
                else:
                    extra = f"- Elapsed: {format_duration(elapsed)}"

                root.after(0, lambda p=percent, d=description, e=extra: update_progress(p, d, e))

    if process.returncode != 0:
        err_msg = "".join(stderr_lines)
        raise Exception(f"FFmpeg Error in {description}:\n{err_msg}")

    root.after(0, lambda: update_progress(100, "Done"))

# ================= AUDIO PROCESS =================
def process_audio(src_video, tgt_video, audio_format, bitrate, sample_rate,
                  lang, mux_video, delay_ms, volume_db, stretch_duration, fast_mode, set_default_track=False, src_track_idx=0, keep_original=True):

    log("Analyzing FPS and duration…")
    fps_src = get_fps(src_video)
    duration_src = get_duration(src_video)
    
    if tgt_video:
        fps_tgt = get_fps(tgt_video)
        duration_tgt = get_duration(tgt_video)
        log(f"Source FPS: {fps_src:.6f}, Target FPS: {fps_tgt:.6f}")
        log(f"Source duration: {format_duration(duration_src)}, Target duration: {format_duration(duration_tgt)}")
    else:
        # No target video provided - operate on Source only (no sync/stretch)
        fps_tgt = fps_src
        duration_tgt = duration_src
        log(f"Source FPS: {fps_src:.6f}")
        log(f"No Target Video provided. Operating in Source-Only mode (Volume Boost / Format Conversion).")
        log(f"Selected Audio Track Index: {src_track_idx + 1}")

    # Determine stretch ratio
    if not tgt_video:
        stretch_ratio = 1.0
        log("Stretch ratio: 1.0 (No Target)")
    elif stretch_duration:
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
    
    # 0. Volume Boost
    try:
        vol_db_val = float(volume_db)
        if abs(vol_db_val) > 0.1:
            log(f"Applying volume boost: {vol_db_val}dB")
            filters.append(f"volume={vol_db_val}dB")
    except ValueError:
        pass
    
    # 1. Stretching
    if fast_mode and abs(stretch_ratio - 1.0) > 1e-6:
        # Fast mode: Use asetrate (resampling) which changes pitch
        # Logic: Play at (sample_rate * ratio), then resample back to sample_rate
        new_rate = int(sample_rate * stretch_ratio)
        log(f"Fast Mode (Pitch Shift): Setting input rate to {new_rate}Hz, then resampling to {sample_rate}Hz")
        filters.append(f"asetrate={new_rate}")
        filters.append(f"aresample={sample_rate}")
    elif abs(stretch_ratio - 1.0) > 1e-6:
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
    
    if audio_format == "mp3":
        ext = "mp3"
        codec = "libmp3lame"
    elif audio_format == "opus":
        ext = "opus"
        codec = "libopus"
    else:
        ext = "aac"
        codec = "aac"

    final_audio = os.path.join(os.path.dirname(src_video), f"{base}_audio.{ext}")
    
    # Step 1: Single Pass Encoding
    total_steps = 2 if mux_video else 1
    current_step = 1

    lang_name, lang_code = parse_language_selection(lang)
    if not lang_code:
        lang_code = "und"

    cmd = [
        FFMPEG, "-y",
        "-i", src_video,
        "-vn", # No video
        "-map", f"0:a:{src_track_idx}", # Select specific audio track
        "-filter:a", filter_str,
        "-c:a", codec,
        "-b:a", bitrate,
        "-ar", str(sample_rate),
        # Use -metadata:s:a:0 because we only have one audio stream in output
        "-metadata:s:a:0", f"language={lang_code}", 
        "-metadata:s:a:0", f"title={lang_name}",
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
        
        # If target video is not provided, use source video as the base for muxing
        target_base_video = tgt_video if tgt_video else src_video
        
        ext = os.path.splitext(target_base_video)[1]
        out_video = os.path.join(
            os.path.dirname(target_base_video),
            f"{os.path.splitext(os.path.basename(target_base_video))[0]}_audio_{lang_name}{ext}"
        )

        # Count existing audio streams
        existing_audio_count = get_audio_stream_count(target_base_video)
        
        # Determine mapping based on keep_original and Source-Only mode
        # Case 1: Source-Only mode (No target video provided)
        if not tgt_video:
             # In Source-Only mode, if keep_original is True, we want to REPLACE the processed track
             # but keep others. If keep_original is False, we keep ONLY the processed track.
             
             if keep_original:
                 # Replace specific track
                 log(f"Source-Only Mode: Replacing track {src_track_idx + 1} with processed audio (keeping others)...")
                 
                 cmd_mux = [
                    FFMPEG, "-y",
                    "-i", target_base_video,
                    "-i", final_audio,
                    "-map", "0:v",
                 ]
                 
                 # Map audio tracks:
                 # Map original tracks BEFORE the target index
                 for i in range(src_track_idx):
                     cmd_mux.extend(["-map", f"0:a:{i}"])
                     cmd_mux.extend(["-c:a", "copy"]) # Copy original tracks
                 
                 # Map the NEW processed track at the target index position
                 cmd_mux.extend(["-map", "1:a"])
                 cmd_mux.extend(["-c:a", "copy"]) # Copy the processed track (it's already encoded)
                 
                 # Map original tracks AFTER the target index
                 for i in range(src_track_idx + 1, existing_audio_count):
                     cmd_mux.extend(["-map", f"0:a:{i}"])
                     cmd_mux.extend(["-c:a", "copy"])

                 # Set metadata for the REPLACED track (which is now at src_track_idx)
                 # Note: The indices in output file correspond to the order we mapped them.
                 # Since we mapped them in order 0..N, the new track is at src_track_idx.
                 cmd_mux.extend([
                    f"-metadata:s:a:{src_track_idx}", f"language={lang_code}",
                    f"-metadata:s:a:{src_track_idx}", f"title={lang_name}",
                    f"-metadata:s:a:{src_track_idx}", f"handler_name={lang_name}"
                 ])
                 
                 # We also need to preserve metadata for other tracks if possible, but -map 0:a:i usually copies metadata.
                 # However, -c:a copy does that.
                 
                 cmd_mux.extend(["-c:v", "copy"]) # Video copy
                 cmd_mux.append(out_video)

             else:
                 # Keep ONLY the processed track (Standard behavior for keep_original=False)
                 new_audio_index = 0
                 log(f"Source-Only Mode: Keeping ONLY processed audio (REMOVING all original tracks)...")
                 cmd_mux = [
                    FFMPEG, "-y",
                    "-i", target_base_video,
                    "-i", final_audio,
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "copy",
                    "-c:a", "copy",
                    f"-metadata:s:a:{new_audio_index}", f"language={lang_code}",
                    f"-metadata:s:a:{new_audio_index}", f"title={lang_name}",
                    f"-metadata:s:a:{new_audio_index}", f"handler_name={lang_name}",
                    out_video
                 ]

        # Case 2: Normal Sync Mode (Target video provided)
        elif keep_original:
            new_audio_index = existing_audio_count  # NEW audio goes last
            log(f"Muxing audio into target video as language={lang_name} ({lang_code}) (keeping {existing_audio_count} original tracks)…")

            cmd_mux = [
                FFMPEG, "-y",
                "-i", target_base_video,
                "-i", final_audio,

                "-map", "0:v",
                "-map", "0:a?", # Map all original audio tracks
                "-map", "1:a",  # Map new audio track

                "-c:v", "copy",
                "-c:a", "copy",

                f"-metadata:s:a:{new_audio_index}", f"language={lang_code}",
                f"-metadata:s:a:{new_audio_index}", f"title={lang_name}",
                f"-metadata:s:a:{new_audio_index}", f"handler_name={lang_name}",

                out_video
            ]
        else:
            new_audio_index = 0 # It will be the only audio track
            log(f"Muxing audio into target video as language={lang_name} ({lang_code}) (REMOVING original tracks)…")

            cmd_mux = [
                FFMPEG, "-y",
                "-i", target_base_video,
                "-i", final_audio,

                "-map", "0:v",
                # "-map", "0:a?", # Do NOT map original audio tracks
                "-map", "1:a",  # Map new audio track only

                "-c:v", "copy",
                "-c:a", "copy",

                f"-metadata:s:a:{new_audio_index}", f"language={lang_code}",
                f"-metadata:s:a:{new_audio_index}", f"title={lang_name}",
                f"-metadata:s:a:{new_audio_index}", f"handler_name={lang_name}",

                out_video
            ]

        if set_default_track:
            log("Setting new audio track as DEFAULT")
            
            # Determine which index is the new track
            if not tgt_video and keep_original:
                target_idx = src_track_idx
            elif not keep_original:
                target_idx = 0
            else:
                target_idx = existing_audio_count

            # If keeping original, we need to unset default for previous tracks
            if keep_original:
                # We need to know total tracks in output to loop correctly
                total_out_tracks = existing_audio_count if not tgt_video else existing_audio_count + 1
                if not tgt_video: total_out_tracks = existing_audio_count # Replaced one, count same
                
                for i in range(total_out_tracks):
                    cmd_mux.insert(-1, f"-disposition:a:{i}")
                    cmd_mux.insert(-1, "0")
            
            cmd_mux.insert(-1, f"-disposition:a:{target_idx}")
            cmd_mux.insert(-1, "default")

        run_ffmpeg_with_progress(cmd_mux, duration_tgt, f"Step {current_step}/{total_steps}: Muxing video")
        log(f"Output video with added audio: {out_video}")

    return final_audio, out_video

# ================= UI LOGIC =================
def start_processing():
    if not vid1_var.get():
        messagebox.showerror("Error", "Please select source video file.")
        return

    log_box.config(state="normal")
    log_box.delete("1.0", tk.END)
    log_box.config(state="disabled")
    btn_start.config(state="disabled")
    btn_stop.config(state="normal")

    audio_format = audio_format_var.get()
    bitrate = bitrate_var.get()
    sample_rate = int(sample_rate_var.get())
    lang = lang_var.get()
    mux_video = mux_var.get()
    delay_ms = int(audio_delay_var.get())
    volume_db = volume_boost_var.get()
    stretch_duration = stretch_duration_var.get()
    fast_mode = fast_mode_var.get()
    set_default = set_default_var.get()
    keep_original = keep_original_var.get()
    
    # Get selected track index
    track_sel = source_audio_track_var.get()
    try:
        # Expected format "Track N: ..." -> index N-1
        if track_sel.startswith("Track "):
            src_track_idx = int(track_sel.split()[1].strip(":")) - 1
        else:
            src_track_idx = 0
    except:
        src_track_idx = 0

    def worker():
        start_time_total = time.time()
        cancel_event.clear()
        try:
            out_audio, out_video = process_audio(
                vid1_var.get(), vid2_var.get(),
                audio_format, bitrate, sample_rate, lang, mux_video,
                delay_ms, volume_db, stretch_duration, fast_mode, set_default,
                src_track_idx, keep_original
            )
            
            elapsed_total = time.time() - start_time_total
            elapsed_str = format_duration(elapsed_total)
            
            log(f"Process Finished. Total Time: {elapsed_str}")
            
            msg = f"Process Finished.\nTotal Time: {elapsed_str}\n\nAudio created:\n{out_audio}"
            if out_video:
                msg += f"\n\nVideo with audio:\n{out_video}"
                
            messagebox.showinfo("Done", msg)
        except Exception as e:
            if str(e) == "Process stopped by user":
                log("Process stopped by user.")
                messagebox.showinfo("Stopped", "Process execution stopped by user.")
            else:
                messagebox.showerror("Error", str(e))
                log(f"ERROR: {e}")
        finally:
            btn_start.config(state="normal")
            btn_stop.config(state="disabled")

    threading.Thread(target=worker, daemon=True).start()

def stop_processing():
    if messagebox.askyesno("Stop", "Are you sure you want to stop the process?"):
        cancel_event.set()

def update_source_tracks(file):
    tracks = get_audio_tracks_info(file)
    cb_audio_tracks['values'] = tracks
    if tracks:
        cb_audio_tracks.current(0)
    else:
        source_audio_track_var.set("No audio tracks found")

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
            update_source_tracks(f)
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
        update_source_tracks(file)

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
source_audio_track_var = tk.StringVar()
audio_format_var = tk.StringVar(value="aac")
bitrate_var = tk.StringVar(value=DEFAULT_BITRATE)
sample_rate_var = tk.StringVar(value=str(DEFAULT_SAMPLE_RATE))
lang_var = tk.StringVar(value="Greek (modern, 1453-) (el, gre)")
mux_var = tk.BooleanVar(value=True)
audio_delay_var = tk.StringVar(value="0")
volume_boost_var = tk.StringVar(value="0")
stretch_duration_var = tk.BooleanVar(value=False)
set_default_var = tk.BooleanVar(value=True)
keep_original_var = tk.BooleanVar(value=True)
status_var = tk.StringVar(value="Ready")
progress_var = tk.DoubleVar(value=0)

# Source video row with frame
tk.Label(root, text="Source Video File").grid(row=0, column=0, sticky="w", padx=5, pady=2)
source_frame = tk.Frame(root)
source_frame.grid(row=0, column=1, columnspan=2, sticky="ew", padx=2)
source_frame.columnconfigure(0, weight=1)
tk.Entry(source_frame, textvariable=vid1_var).grid(row=0, column=0, sticky="ew")
tk.Button(source_frame, text="Browse", command=browse_source, width=12).grid(row=0, column=1, sticky="e", padx=5)

# Source Audio Track Selection
tk.Label(root, text="Source Audio Track").grid(row=1, column=0, sticky="w", padx=5, pady=2)
source_audio_frame = tk.Frame(root)
source_audio_frame.grid(row=1, column=1, columnspan=2, sticky="ew", padx=2)
source_audio_frame.columnconfigure(0, weight=1)
cb_audio_tracks = ttk.Combobox(source_audio_frame, textvariable=source_audio_track_var, state="readonly")
cb_audio_tracks.grid(row=0, column=0, sticky="ew", padx=(0, 5))

# Target video row with frame
tk.Label(root, text="Target Video File").grid(row=2, column=0, sticky="w", padx=5, pady=2)
target_frame = tk.Frame(root)
target_frame.grid(row=2, column=1, columnspan=2, sticky="ew", padx=2)
target_frame.columnconfigure(0, weight=1)
tk.Entry(target_frame, textvariable=vid2_var).grid(row=0, column=0, sticky="ew")
tk.Button(target_frame, text="Browse", command=browse_target, width=12).grid(row=0, column=1, sticky="e", padx=5)

# Audio options
tk.Label(root, text="Audio Format").grid(row=3, column=0, sticky="w", padx=5, pady=2)
ttk.Combobox(root, textvariable=audio_format_var, values=["mp3", "aac", "opus"], state="readonly").grid(row=3, column=1, sticky="w", padx=2)

tk.Label(root, text="Bitrate").grid(row=4, column=0, sticky="w", padx=5, pady=2)
ttk.Combobox(root, textvariable=bitrate_var, values=["128k","192k","256k","320k"], state="readonly").grid(row=4, column=1, sticky="w", padx=2)

# Volume Boost
vol_frame = tk.Frame(root)
vol_frame.grid(row=4, column=2, sticky="w", padx=5)
tk.Label(vol_frame, text="Vol Boost (dB):").pack(side="left")
vol_values = ["-20", "-15", "-12", "-10", "-9", "-6", "-5", "-4", "-3", "-2", "-1", "0", "1", "2", "3", "4", "5", "6", "9", "10", "12", "15", "20"]
ttk.Combobox(vol_frame, textvariable=volume_boost_var, values=vol_values, width=5).pack(side="left", padx=2)

tk.Label(root, text="Sample Rate (Hz)").grid(row=5, column=0, sticky="w", padx=5, pady=2)
ttk.Combobox(root, textvariable=sample_rate_var, values=["44100","48000"], state="readonly").grid(row=5, column=1, sticky="w", padx=2)

# Audio language
tk.Label(root, text="Audio Language").grid(row=6, column=0, sticky="w", padx=5, pady=2)
languages = [
    "Abkhazian (abk)", "Afar (aar)", "Afrikaans (afr)", "Akan (aka)", "Albanian (sqi)", "Amharic (amh)", "Arabic (ara)", "Aragonese (arg)", "Armenian (hye)", "Assamese (asm)", "Avaric (ava)", "Avestan (ave)", "Aymara (aym)", "Azerbaijani (aze)", 
    "Bambara (bam)", "Bashkir (bak)", "Basque (eus)", "Belarusian (bel)", "Bengali (ben)", "Bihari languages (bih)", "Bislama (bis)", "Bosnian (bos)", "Breton (bre)", "Bulgarian (bul)", "Burmese (mya)", 
    "Catalan (cat)", "Chamorro (cha)", "Chechen (che)", "Chichewa (nyā)", "Chinese (zho)", "Church Slavic (chu)", "Chuvash (chv)", "Cornish (cor)", "Corsican (cos)", "Cree (cre)", "Croatian (hrv)", "Czech (ces)", 
    "Danish (dan)", "Divehi (div)", "Dutch (nld)", "Dzongkha (dzo)", 
    "English (eng)", "Esperanto (epo)", "Estonian (est)", "Ewe (ewe)", 
    "Faroese (fao)", "Fijian (fij)", "Finnish (fin)", "French (fra)", "Fulah (ful)", 
    "Galician (glg)", "Ganda (lug)", "Georgian (kat)", "German (deu)", "Greek (ell)", "Guarani (grn)", "Gujarati (guj)", 
    "Haitian (hat)", "Hausa (hau)", "Hebrew (heb)", "Herero (her)", "Hindi (hin)", "Hiri Motu (hmo)", "Hungarian (hun)", 
    "Icelandic (isl)", "Ido (ido)", "Igbo (ibo)", "Indonesian (ind)", "Interlingua (ina)", "Interlingue (ile)", "Inuktitut (iku)", "Inupiaq (ipk)", "Irish (gle)", "Italian (ita)", 
    "Japanese (jpn)", "Javanese (jav)", 
    "Kalaallisut (kal)", "Kannada (kan)", "Kanuri (kau)", "Kashmiri (kas)", "Kazakh (kaz)", "Khmer (khm)", "Kikuyu (kik)", "Kinyarwanda (kin)", "Kirghiz (kir)", "Komi (kom)", "Kongo (kon)", "Korean (kor)", "Kuanyama (kua)", "Kurdish (kur)", 
    "Lao (lao)", "Latin (lat)", "Latvian (lav)", "Limburgan (lim)", "Lingala (lin)", "Lithuanian (lit)", "Luba-Katanga (lub)", "Luxembourgish (ltz)", 
    "Macedonian (mkd)", "Malagasy (mlg)", "Malay (msa)", "Malayalam (mal)", "Maltese (mlt)", "Manx (glv)", "Maori (mri)", "Marathi (mar)", "Marshallese (mah)", "Mongolian (mon)", 
    "Nauru (nau)", "Navajo (nav)", "Ndebele, North (nde)", "Ndebele, South (nbl)", "Ndonga (ndo)", "Nepali (nep)", "Northern Sami (sme)", "Norwegian (nor)", "Norwegian Bokmål (nob)", "Norwegian Nynorsk (nno)", 
    "Occitan (oci)", "Ojibwa (oji)", "Oriya (ori)", "Oromo (orm)", "Ossetian (oss)", 
    "Pali (pli)", "Pashto (pus)", "Persian (fas)", "Polish (pol)", "Portuguese (por)", "Punjabi (pan)", 
    "Quechua (que)", 
    "Romanian (ron)", "Romansh (roh)", "Rundi (run)", "Russian (rus)", 
    "Samoan (smo)", "Sango (sag)", "Sanskrit (san)", "Sardinian (srd)", "Scottish Gaelic (gla)", "Serbian (srp)", "Shona (sna)", "Sichuan Yi (iii)", "Sindhi (snd)", "Sinhala (sin)", "Slovak (slk)", "Slovenian (slv)", "Somali (som)", "Sotho, Southern (sot)", "Spanish (spa)", "Sundanese (sun)", "Swahili (swa)", "Swati (ssw)", "Swedish (swe)", 
    "Tagalog (tgl)", "Tahitian (tah)", "Tajik (tgk)", "Tamil (tam)", "Tatar (tat)", "Telugu (tel)", "Thai (tha)", "Tibetan (bod)", "Tigrinya (tir)", "Tonga (ton)", "Tsonga (tso)", "Tswana (tsn)", "Turkish (tur)", "Turkmen (tuk)", "Twi (twi)", 
    "Uighur (uig)", "Ukrainian (ukr)", "Urdu (urd)", "Uzbek (uzb)", 
    "Venda (ven)", "Vietnamese (vie)", "Volapük (vol)", 
    "Walloon (wln)", "Welsh (cym)", "Western Frisian (fry)", "Wolof (wol)", 
    "Xhosa (xho)", 
    "Yiddish (yid)", "Yoruba (yor)", 
    "Zhuang (zha)", "Zulu (zul)"
]
ttk.Combobox(root, textvariable=lang_var, values=languages, state="readonly").grid(row=6, column=1, sticky="w", padx=2)

# Mux options frame
mux_frame = tk.Frame(root)
mux_frame.grid(row=6, column=2, sticky="e", padx=5)
tk.Checkbutton(mux_frame, text="Mux audio", variable=mux_var).pack(side="left")
tk.Checkbutton(mux_frame, text="Set Default", variable=set_default_var).pack(side="left", padx=5)
tk.Checkbutton(mux_frame, text="Keep Tracks", variable=keep_original_var).pack(side="left", padx=5)

# Audio delay input
tk.Label(root, text="Audio Delay (ms)").grid(row=7, column=0, sticky="w", padx=5, pady=2)
tk.Entry(root, textvariable=audio_delay_var).grid(row=7, column=1, sticky="w", padx=2)

# Stretch options frame
stretch_frame = tk.Frame(root)
stretch_frame.grid(row=7, column=2, sticky="w", padx=5)

# Stretch duration checkbox
tk.Checkbutton(stretch_frame, text="Stretch to exact duration",
               variable=stretch_duration_var).pack(side="left")

# Fast mode checkbox
fast_mode_var = tk.BooleanVar(value=False)
tk.Checkbutton(stretch_frame, text="Fast Mode (Pitch Shift)",
               variable=fast_mode_var).pack(side="left", padx=5)

# Drag & drop area
drop = tk.Label(root, text="Drag & drop two videos here", relief="groove", height=3)
drop.grid(row=8, column=0, columnspan=3, sticky="ew", padx=5, pady=4)
drop.drop_target_register(DND_FILES) # type: ignore
drop.dnd_bind("<<Drop>>", on_drop) # type: ignore

# Start/Stop buttons
btn_frame = tk.Frame(root)
btn_frame.grid(row=9, column=0, columnspan=3, pady=6, sticky="ew", padx=5)
btn_frame.columnconfigure(0, weight=1)
btn_frame.columnconfigure(1, weight=1)

btn_start = ttk.Button(btn_frame, text="Start Processing", command=start_processing)
btn_start.grid(row=0, column=0, sticky="ew", padx=2)

btn_stop = ttk.Button(btn_frame, text="Stop Processing", command=stop_processing, state="disabled")
btn_stop.grid(row=0, column=1, sticky="ew", padx=2)

# Status and Progress
tk.Label(root, textvariable=status_var).grid(row=10, column=0, columnspan=3, sticky="w", padx=5)
ttk.Progressbar(root, variable=progress_var, maximum=100).grid(row=11, column=0, columnspan=3, sticky="ew", padx=5, pady=2)

# Log panel
log_box = tk.Text(root, height=14)
log_box.grid(row=12, column=0, columnspan=3, sticky="nsew", padx=5, pady=4)
log_box.config(state="disabled")

root.mainloop()
