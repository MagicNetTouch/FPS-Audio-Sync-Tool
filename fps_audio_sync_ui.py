import ctypes
import os, sys, json, threading, subprocess, re, time, queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES # type: ignore

# ================= CONFIG =================
APP_NAME = "FPS Audio Sync Tool"
APP_VERSION = "2.5"
APP_AUTHOR = "Gant"
APP_ID = "Gant.FPSAudioSyncTool"
APP_WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION} by {APP_AUTHOR}"
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_BITRATE = "192k"

TRANSLATIONS = {
    "en": {
        "missing_tools_title": "Missing Tools",
        "missing_tools": "FFmpeg tools were not found.\n\nPlace ffmpeg.exe and ffprobe.exe in:\n{preferred}\n\nor beside the application in:\n{app_folder}",
        "error": "Error", "done": "Done", "stopped": "Stopped", "stop": "Stop",
        "ready": "Ready", "starting": "Starting...",
        "source_video": "Source Video File", "source_track": "Source Audio Track",
        "target_video": "Target Video File", "audio_format": "Audio Format",
        "bitrate": "Bitrate", "volume_boost": "Vol Boost (dB):",
        "sample_rate": "Sample Rate (Hz)", "audio_language": "Audio Language",
        "search_language": "Search language:", "mux_audio": "Mux audio",
        "set_default": "Set Default", "keep_tracks": "Keep Tracks",
        "audio_delay": "Audio Delay (ms)", "stretch_duration": "Stretch to exact duration",
        "fast_mode": "Fast Mode (Pitch Shift)", "output_video": "Output Video File",
        "browse": "Browse", "auto": "Auto",
        "drop_files": "Drag & drop source and target videos here",
        "start_processing": "Start Processing", "stop_processing": "Stop Processing",
        "save_default": "Save Default", "load_default": "Load Default",
        "save_as": "Save...", "load_from": "Load...", "reset": "Reset",
        "interface_language": "Interface:", "english": "English", "greek": "Ελληνικά",
        "select_source": "Please select source video file.",
        "whole_numbers": "Sample rate and audio delay must be whole numbers.",
        "confirm_stop": "Are you sure you want to stop the process?",
        "no_tracks": "No audio tracks found",
        "select_output": "Select Output Video File", "select_source_file": "Select Source Video File",
        "select_target_file": "Select Target Video File", "video_files": "Video Files",
        "all_files": "All Files", "json_files": "JSON Files",
        "save_settings": "Save Settings", "load_settings": "Load Settings",
        "settings_missing": "Default settings file not found:\n{path}",
        "save_failed": "Failed to save settings:\n{error}",
        "load_failed": "Failed to load settings:\n{error}",
        "loading_file": "Loading {role} file: {name}...",
        "loaded_file": "Loaded {role} file: {name}",
        "failed_file": "Failed to load {role} file",
        "source_role": "source", "target_role": "target",
        "process_finished": "Process Finished.", "total_time": "Total Time: {time}",
        "audio_created": "Audio created:", "video_created": "Video with audio:",
        "stopped_message": "Process execution stopped by user.",
    },
    "el": {
        "missing_tools_title": "Λείπουν εργαλεία",
        "missing_tools": "Δεν βρέθηκαν τα εργαλεία FFmpeg.\n\nΤοποθετήστε τα ffmpeg.exe και ffprobe.exe στο:\n{preferred}\n\nή δίπλα στην εφαρμογή στο:\n{app_folder}",
        "error": "Σφάλμα", "done": "Ολοκληρώθηκε", "stopped": "Διακόπηκε", "stop": "Διακοπή",
        "ready": "Έτοιμο", "starting": "Εκκίνηση...",
        "source_video": "Αρχείο βίντεο πηγής", "source_track": "Κομμάτι ήχου πηγής",
        "target_video": "Αρχείο βίντεο στόχου", "audio_format": "Μορφή ήχου",
        "bitrate": "Ρυθμός μετάδοσης", "volume_boost": "Ενίσχυση (dB):",
        "sample_rate": "Ρυθμός δειγματοληψίας (Hz)", "audio_language": "Γλώσσα ήχου",
        "search_language": "Αναζήτηση γλώσσας:", "mux_audio": "Ενσωμάτωση ήχου",
        "set_default": "Προεπιλογή", "keep_tracks": "Διατήρηση κομματιών",
        "audio_delay": "Καθυστέρηση ήχου (ms)", "stretch_duration": "Προσαρμογή στην ακριβή διάρκεια",
        "fast_mode": "Γρήγορη λειτουργία (αλλαγή τόνου)", "output_video": "Αρχείο βίντεο εξόδου",
        "browse": "Αναζήτηση", "auto": "Αυτόματο",
        "drop_files": "Σύρετε εδώ τα βίντεο πηγής και στόχου",
        "start_processing": "Έναρξη επεξεργασίας", "stop_processing": "Διακοπή επεξεργασίας",
        "save_default": "Αποθ. προεπιλογών", "load_default": "Φόρτ. προεπιλογών",
        "save_as": "Αποθήκευση...", "load_from": "Φόρτωση...", "reset": "Επαναφορά",
        "interface_language": "Περιβάλλον:", "english": "English", "greek": "Ελληνικά",
        "select_source": "Επιλέξτε αρχείο βίντεο πηγής.",
        "whole_numbers": "Ο ρυθμός δειγματοληψίας και η καθυστέρηση ήχου πρέπει να είναι ακέραιοι αριθμοί.",
        "confirm_stop": "Θέλετε σίγουρα να διακόψετε τη διαδικασία;",
        "no_tracks": "Δεν βρέθηκαν κομμάτια ήχου",
        "select_output": "Επιλογή αρχείου βίντεο εξόδου", "select_source_file": "Επιλογή βίντεο πηγής",
        "select_target_file": "Επιλογή βίντεο στόχου", "video_files": "Αρχεία βίντεο",
        "all_files": "Όλα τα αρχεία", "json_files": "Αρχεία JSON",
        "save_settings": "Αποθήκευση ρυθμίσεων", "load_settings": "Φόρτωση ρυθμίσεων",
        "settings_missing": "Δεν βρέθηκε το αρχείο προεπιλεγμένων ρυθμίσεων:\n{path}",
        "save_failed": "Αποτυχία αποθήκευσης ρυθμίσεων:\n{error}",
        "load_failed": "Αποτυχία φόρτωσης ρυθμίσεων:\n{error}",
        "loading_file": "Φόρτωση αρχείου {role}: {name}...",
        "loaded_file": "Φορτώθηκε το αρχείο {role}: {name}",
        "failed_file": "Αποτυχία φόρτωσης αρχείου {role}",
        "source_role": "πηγής", "target_role": "στόχου",
        "process_finished": "Η διαδικασία ολοκληρώθηκε.", "total_time": "Συνολικός χρόνος: {time}",
        "audio_created": "Δημιουργήθηκε ήχος:", "video_created": "Βίντεο με ήχο:",
        "stopped_message": "Η διαδικασία διακόπηκε από τον χρήστη.",
    },
}

_active_ui_language = "en"

def tr(key, **kwargs):
    language = _active_ui_language
    text = TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text

# ================= BUNDLED PATHS =================
def bundled_path(*parts):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, *parts) # type: ignore[attr-defined]
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts)

def executable_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def external_tool_path(filename):
    app_folder = executable_dir()
    candidates = [
        os.path.join(app_folder, "tools", filename),
        os.path.join(app_folder, filename),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    # Use the preferred location in any resulting error message.
    return candidates[0]

def set_windows_app_id():
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass

APP_ICON = bundled_path("assets", "app_icon.ico")
FFMPEG = external_tool_path("ffmpeg.exe")
FFPROBE = external_tool_path("ffprobe.exe")
SUBPROCESS_WINDOW_OPTIONS = (
    {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
)

def require_media_tools():
    missing = [path for path in (FFMPEG, FFPROBE) if not os.path.isfile(path)]
    if not missing:
        return True
    app_folder = executable_dir()
    preferred = os.path.join(app_folder, "tools")
    messagebox.showerror(
        tr("missing_tools_title"),
        tr("missing_tools", preferred=preferred, app_folder=app_folder)
    )
    return False

# ================= LOGGING =================
ui_queue = queue.Queue()

def post_ui(callback, *args, **kwargs):
    """Queue a callback for execution by Tk's main thread."""
    ui_queue.put((callback, args, kwargs))

def _append_log(msg):
    log_box.config(state="normal")
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    log_box.config(state="disabled")

def log(msg):
    if threading.current_thread() is threading.main_thread():
        _append_log(msg)
    else:
        post_ui(_append_log, msg)

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
    r = subprocess.run(cmd, capture_output=True, text=True, check=True,
                       **SUBPROCESS_WINDOW_OPTIONS)
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
    r = subprocess.run(cmd, capture_output=True, text=True, check=True,
                       **SUBPROCESS_WINDOW_OPTIONS)
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
    r = subprocess.run(cmd, capture_output=True, text=True, check=True,
                       **SUBPROCESS_WINDOW_OPTIONS)
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
        r = subprocess.run(cmd, capture_output=True, text=True, check=True,
                           **SUBPROCESS_WINDOW_OPTIONS)
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

LANGUAGE_FILENAME_CODES = {
    "eng": "EN", "ell": "GR", "gre": "GR", "deu": "DE", "ger": "DE",
    "fra": "FR", "fre": "FR", "spa": "ES", "ita": "IT", "por": "PT",
    "nld": "NL", "dut": "NL", "rus": "RU", "ukr": "UA", "pol": "PL",
    "tur": "TR", "ara": "AR", "heb": "HE", "hin": "HI", "jpn": "JA",
    "kor": "KO", "zho": "ZH", "chi": "ZH", "ces": "CS", "cze": "CS",
    "swe": "SV", "nor": "NO", "dan": "DA", "fin": "FI", "ron": "RO",
    "rum": "RO", "bul": "BG", "hrv": "HR", "srp": "SR", "slk": "SK",
    "slv": "SL", "hun": "HU", "ind": "ID", "tha": "TH", "vie": "VI",
}

def language_filename_code(code):
    code = (code or "und").strip().lower().split("-")[0]
    if code in LANGUAGE_FILENAME_CODES:
        return LANGUAGE_FILENAME_CODES[code]
    if len(code) == 2 and code.isalpha():
        return code.upper()
    if len(code) == 3 and code.isalpha():
        return code.upper()
    return "UND"

def get_audio_language_codes(video_path):
    cmd = [
        FFPROBE, "-v", "error", "-select_streams", "a",
        "-show_entries", "stream_tags=language", "-of", "json", video_path
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True,
                           **SUBPROCESS_WINDOW_OPTIONS)
        streams = json.loads(r.stdout).get("streams", [])
        return [
            language_filename_code((stream.get("tags") or {}).get("language"))
            for stream in streams
        ]
    except Exception:
        return []

def build_output_video_path(src_video, tgt_video, new_lang_code,
                            keep_original, src_track_idx):
    base_video = tgt_video if tgt_video else src_video
    languages = get_audio_language_codes(base_video) if keep_original else []
    new_code = language_filename_code(new_lang_code)

    if not tgt_video and keep_original:
        if 0 <= src_track_idx < len(languages):
            languages[src_track_idx] = new_code
        else:
            languages.append(new_code)
    else:
        languages.append(new_code)

    # Keep the filename readable when multiple tracks use the same language.
    languages = list(dict.fromkeys(languages or [new_code]))
    suffix = "-".join(languages)
    folder = os.path.dirname(base_video)
    base, ext = os.path.splitext(os.path.basename(base_video))
    return os.path.normpath(os.path.join(folder, f"{base}_{suffix}{ext}"))

def get_audio_stream_count(video_path):
    cmd = [
        FFPROBE, "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index",
        "-of", "json",
        video_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True,
                       **SUBPROCESS_WINDOW_OPTIONS)
    data = json.loads(r.stdout)
    return len(data.get("streams", []))

def update_progress(val, text, extra=""):
    progress_var.set(val)
    status_var.set(f"{text}: {val:.1f}% {extra}".strip())

cancel_event = threading.Event()
process_lock = threading.Lock()
active_process = None
processing_thread = None

class ProcessingCancelled(Exception):
    pass

def _set_active_process(process):
    global active_process
    with process_lock:
        active_process = process

def _clear_active_process(process):
    global active_process
    with process_lock:
        if active_process is process:
            active_process = None

def _terminate_process(process):
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    except OSError:
        pass

def _signal_process_stop(process):
    """Request termination without blocking Tk's main thread."""
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
    except OSError:
        pass

def run_ffmpeg_with_progress(cmd, total_duration, description):
    log(f"{description}...")
    post_ui(update_progress, 0, description)

    if cancel_event.is_set():
        raise ProcessingCancelled("Process stopped by user")

    start_time = time.time()

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace',
        **SUBPROCESS_WINDOW_OPTIONS
    )
    _set_active_process(process)

    try:
        if process.stderr is None:
            raise RuntimeError(f"Failed to open stderr for {description}")

        stderr_pipe = process.stderr

        # Use deque to keep only recent lines and avoid slicing issues
        from collections import deque
        stderr_lines = deque(maxlen=20)
        pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")

        while True:
            if cancel_event.is_set():
                _terminate_process(process)
                raise ProcessingCancelled("Process stopped by user")

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

                    post_ui(update_progress, percent, description, extra)

        if process.returncode != 0:
            if cancel_event.is_set():
                raise ProcessingCancelled("Process stopped by user")
            err_msg = "".join(stderr_lines)
            raise Exception(f"FFmpeg Error in {description}:\n{err_msg}")

        post_ui(update_progress, 100, "Done")
    finally:
        _clear_active_process(process)
        if process.poll() is None:
            _terminate_process(process)

# ================= AUDIO PROCESS =================
def process_audio(src_video, tgt_video, audio_format, bitrate, sample_rate,
                  lang, mux_video, delay_ms, volume_db, stretch_duration,
                  fast_mode, set_default_track=False, src_track_idx=0,
                  keep_original=True, output_video=""):

    log("Analyzing FPS and duration…")
    source_name = os.path.basename(src_video)
    post_ui(update_progress, 0, f"Analyzing source file: {source_name}")
    log(f"Analyzing source file: {source_name}...")
    fps_src = get_fps(src_video)
    duration_src = get_duration(src_video)
    
    if tgt_video:
        target_name = os.path.basename(tgt_video)
        post_ui(update_progress, 0, f"Analyzing target file: {target_name}")
        log(f"Analyzing target file: {target_name}...")
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
        
        out_video = output_video or build_output_video_path(
            src_video, tgt_video, lang_code, keep_original, src_track_idx
        )
        out_video = os.path.abspath(out_video)
        if os.path.normcase(out_video) == os.path.normcase(os.path.abspath(target_base_video)):
            raise ValueError("The output video cannot overwrite the source or target input file.")
        os.makedirs(os.path.dirname(out_video), exist_ok=True)

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
    global processing_thread

    if processing_thread is not None and processing_thread.is_alive():
        return

    if not require_media_tools():
        return

    if not vid1_var.get():
        messagebox.showerror(tr("error"), tr("select_source"))
        return

    try:
        source_video = vid1_var.get()
        target_video = vid2_var.get()
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
    except ValueError:
        messagebox.showerror(tr("error"), tr("whole_numbers"))
        return
    
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

    output_video = ""
    if mux_video:
        if not output_path_state["custom"] or not output_video_var.get().strip():
            _, selected_lang_code = parse_language_selection(lang)
            output_video = build_output_video_path(
                source_video, target_video, selected_lang_code,
                keep_original, src_track_idx
            )
            output_video_var.set(output_video)
        else:
            output_video = output_video_var.get().strip()

    log_box.config(state="normal")
    log_box.delete("1.0", tk.END)
    log_box.config(state="disabled")
    progress_var.set(0)
    status_var.set(tr("starting"))
    btn_start.config(state="disabled")
    btn_stop.config(state="normal")
    cancel_event.clear()

    def worker():
        start_time_total = time.time()
        try:
            out_audio, out_video = process_audio(
                source_video, target_video,
                audio_format, bitrate, sample_rate, lang, mux_video,
                delay_ms, volume_db, stretch_duration, fast_mode, set_default,
                src_track_idx, keep_original, output_video
            )
            
            elapsed_total = time.time() - start_time_total
            elapsed_str = format_duration(elapsed_total)
            
            log(f"Process Finished. Total Time: {elapsed_str}")
            
            msg = f"{tr('process_finished')}\n{tr('total_time', time=elapsed_str)}\n\n{tr('audio_created')}\n{out_audio}"
            if out_video:
                msg += f"\n\n{tr('video_created')}\n{out_video}"
                
            post_ui(_finish_processing, "done", msg)
        except ProcessingCancelled:
            log("Process stopped by user.")
            post_ui(_finish_processing, "stopped", tr("stopped_message"))
        except Exception as e:
            if cancel_event.is_set():
                log("Process stopped by user.")
                post_ui(_finish_processing, "stopped", tr("stopped_message"))
            else:
                log(f"ERROR: {e}")
                post_ui(_finish_processing, "error", str(e))

    processing_thread = threading.Thread(target=worker, daemon=True)
    processing_thread.start()

def _finish_processing(result, message):
    global processing_thread
    processing_thread = None
    btn_start.config(state="normal")
    btn_stop.config(state="disabled")
    if result == "done":
        messagebox.showinfo(tr("done"), message)
    elif result == "stopped":
        status_var.set(tr("stopped"))
        messagebox.showinfo(tr("stopped"), message)
    else:
        status_var.set(tr("error"))
        messagebox.showerror(tr("error"), message)

def stop_processing():
    if messagebox.askyesno(tr("stop"), tr("confirm_stop")):
        cancel_event.set()
        with process_lock:
            process = active_process
        _signal_process_stop(process)

def update_source_tracks(file):
    tracks = get_audio_tracks_info(file)
    cb_audio_tracks['values'] = tracks
    if tracks:
        cb_audio_tracks.current(0)
    else:
        source_audio_track_var.set(tr("no_tracks"))

def selected_source_track_index():
    track_sel = source_audio_track_var.get()
    try:
        if track_sel.startswith("Track "):
            return int(track_sel.split()[1].strip(":")) - 1
    except (ValueError, IndexError):
        pass
    return 0

def refresh_auto_output_path():
    if output_path_state["custom"] or not mux_var.get() or not vid1_var.get():
        return
    _, lang_code = parse_language_selection(lang_var.get())
    output_video_var.set(build_output_video_path(
        vid1_var.get(), vid2_var.get(), lang_code,
        keep_original_var.get(), selected_source_track_index()
    ))

def browse_output_video():
    suggested = output_video_var.get().strip()
    if not suggested and vid1_var.get():
        output_path_state["custom"] = False
        refresh_auto_output_path()
        suggested = output_video_var.get().strip()

    base_video = vid2_var.get() or vid1_var.get()
    initial_dir = os.path.dirname(suggested or base_video) if base_video else ""
    initial_file = os.path.basename(suggested) if suggested else ""
    path = filedialog.asksaveasfilename(
        title=tr("select_output"),
        initialdir=initial_dir,
        initialfile=initial_file,
        defaultextension=os.path.splitext(base_video)[1] if base_video else ".mkv",
        filetypes=[(tr("video_files"), "*.mkv *.mp4 *.mov *.avi *.webm"), (tr("all_files"), "*.*")]
    )
    if path:
        output_path_state["custom"] = True
        output_video_var.set(path)

def use_auto_output_path():
    output_path_state["custom"] = False
    refresh_auto_output_path()

def mark_output_path_custom(_event=None):
    output_path_state["custom"] = bool(output_video_var.get().strip())

def load_video_file(file, is_source):
    if not require_media_tools():
        return False

    role = tr("source_role" if is_source else "target_role")
    name = os.path.basename(file)
    status_var.set(tr("loading_file", role=role, name=name))
    progress_var.set(0)
    root.update_idletasks()

    try:
        fps = get_fps(file)
        duration = get_duration(file)
        codec = get_video_codec(file)
        if is_source:
            vid1_var.set(file)
            update_source_tracks(file)
        else:
            vid2_var.set(file)
        log(
            f"Loaded {role.title()} Video File: {name} / FPS: {fps:.6f} / "
            f"Duration: {format_duration(duration)} / Codec: {codec}"
        )
        refresh_auto_output_path()
        status_var.set(tr("loaded_file", role=role, name=name))
        return True
    except Exception as e:
        status_var.set(tr("failed_file", role=role))
        log(f"ERROR loading {role} file: {e}")
        messagebox.showerror(tr("error"), f"{tr('failed_file', role=role)}:\n{e}")
        return False

def on_drop(event):
    files = root.tk.splitlist(event.data)
    for f in files:
        if not vid1_var.get():
            load_video_file(f, True)
        elif not vid2_var.get():
            load_video_file(f, False)
        else:
            break

def browse_source():
    file = filedialog.askopenfilename(title=tr("select_source_file"),
                                      filetypes=[(tr("video_files"), "*.mp4 *.mkv *.mov *.avi *.flv *.webm")])
    if file:
        load_video_file(file, True)

def browse_target():
    file = filedialog.askopenfilename(title=tr("select_target_file"),
                                      filetypes=[(tr("video_files"), "*.mp4 *.mkv *.mov *.avi *.flv *.webm")])
    if file:
        load_video_file(file, False)

def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

DEFAULT_SETTINGS_PATH = os.path.join(_app_dir(), "default_settings.json")

def _bool_value(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False

def _collect_settings():
    return {
        "audio_format": audio_format_var.get(),
        "bitrate": bitrate_var.get(),
        "sample_rate": sample_rate_var.get(),
        "lang": lang_var.get(),
        "mux": mux_var.get(),
        "set_default": set_default_var.get(),
        "keep_original": keep_original_var.get(),
        "delay_ms": audio_delay_var.get(),
        "volume_db": volume_boost_var.get(),
        "stretch_duration": stretch_duration_var.get(),
        "fast_mode": fast_mode_var.get(),
        "ui_language": ui_language_var.get(),
    }

def _apply_settings(data):
    if not isinstance(data, dict):
        return
    if "audio_format" in data:
        audio_format_var.set(str(data["audio_format"]))
    if "bitrate" in data:
        bitrate_var.set(str(data["bitrate"]))
    if "sample_rate" in data:
        sample_rate_var.set(str(data["sample_rate"]))
    if "lang" in data:
        lang_var.set(str(data["lang"]))
    if "mux" in data:
        mux_var.set(_bool_value(data["mux"]))
    if "set_default" in data:
        set_default_var.set(_bool_value(data["set_default"]))
    if "keep_original" in data:
        keep_original_var.set(_bool_value(data["keep_original"]))
    if "delay_ms" in data:
        audio_delay_var.set(str(data["delay_ms"]))
    if "volume_db" in data:
        volume_boost_var.set(str(data["volume_db"]))
    if "stretch_duration" in data:
        stretch_duration_var.set(_bool_value(data["stretch_duration"]))
    if "fast_mode" in data:
        fast_mode_var.set(_bool_value(data["fast_mode"]))
    if "ui_language" in data and str(data["ui_language"]) in TRANSLATIONS:
        ui_language_var.set(str(data["ui_language"]))

def _save_settings_to(path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_collect_settings(), f, ensure_ascii=False, indent=2)
        log(f"Settings saved: {path}")
    except Exception as e:
        messagebox.showerror(tr("error"), tr("save_failed", error=e))

def _load_settings_from(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _apply_settings(data)
        log(f"Settings loaded: {path}")
    except Exception as e:
        messagebox.showerror(tr("error"), tr("load_failed", error=e))

def save_default_settings():
    _save_settings_to(DEFAULT_SETTINGS_PATH)

def load_default_settings():
    if not os.path.exists(DEFAULT_SETTINGS_PATH):
        messagebox.showerror(tr("error"), tr("settings_missing", path=DEFAULT_SETTINGS_PATH))
        return
    _load_settings_from(DEFAULT_SETTINGS_PATH)

def _load_default_settings_on_startup():
    if not os.path.exists(DEFAULT_SETTINGS_PATH):
        return
    try:
        with open(DEFAULT_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        _apply_settings(data)
    except Exception:
        return

def save_settings_as():
    path = filedialog.asksaveasfilename(
        title=tr("save_settings"),
        defaultextension=".json",
        filetypes=[(tr("json_files"), "*.json")],
    )
    if path:
        _save_settings_to(path)

def load_settings_from():
    path = filedialog.askopenfilename(
        title=tr("load_settings"),
        filetypes=[(tr("json_files"), "*.json")],
    )
    if path:
        _load_settings_from(path)

def reset_settings_to_initial():
    audio_format_var.set("aac")
    bitrate_var.set(DEFAULT_BITRATE)
    sample_rate_var.set(str(DEFAULT_SAMPLE_RATE))
    try:
        if "Greek (ell)" in languages:
            lang_var.set("Greek (ell)")
        else:
            lang_var.set("English (eng)")
    except Exception:
        lang_var.set("English (eng)")
    mux_var.set(True)
    set_default_var.set(True)
    keep_original_var.set(True)
    audio_delay_var.set("0")
    volume_boost_var.set("0")
    stretch_duration_var.set(False)
    if "fast_mode_var" in globals():
        fast_mode_var.set(False)

# ================= UI =================
THEME_BG = "#0b0f17"
THEME_SURFACE = "#141a24"
THEME_INPUT = "#1a2230"
THEME_BORDER = "#2a3547"
THEME_TEXT = "#f3f6fb"
THEME_MUTED = "#9aa8ba"
THEME_ACCENT = "#5b8cff"
THEME_ACCENT_HOVER = "#76a0ff"
THEME_DANGER = "#e05263"
THEME_DANGER_HOVER = "#ef6a79"
THEME_SHADOW = "#05070b"

class ShadowButton(tk.Canvas):
    """Rounded dark-theme button with a drawn shadow and hover states."""
    def __init__(self, parent, text, command=None, width=104, height=28,
                 color=THEME_ACCENT, hover_color=THEME_ACCENT_HOVER,
                 state="normal"):
        super().__init__(
            parent, width=width, height=height, background=THEME_BG,
            highlightthickness=0, borderwidth=0, cursor="hand2"
        )
        self._text = text
        self._command = command
        self._color = color
        self._hover_color = hover_color
        self._state = state
        self._hovered = False
        self._pressed = False
        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.after_idle(self._redraw)

    def _rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1,
            x2, y1 + radius, x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2, x1, y2,
            x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, splinesteps=18, **kwargs)

    def _redraw(self, _event=None):
        self.delete("all")
        width = max(20, self.winfo_width())
        height = max(20, self.winfo_height())
        disabled = self._state == "disabled"
        offset = 2 if self._pressed and not disabled else 0
        color = "#303a49" if disabled else (
            self._hover_color if self._hovered else self._color
        )
        text_color = "#7d8795" if disabled else "#ffffff"
        self._rounded_rectangle(3, 4, width - 2, height - 1, 6,
                                fill=THEME_SHADOW, outline="")
        self._rounded_rectangle(1, 1 + offset, width - 4, height - 4 + offset, 6,
                                fill=color, outline="")
        self.create_text(width / 2 - 1, (height - 4) / 2 + offset,
                         text=self._text, fill=text_color,
                         font=("Segoe UI Semibold", 9))

    def _on_enter(self, _event=None):
        self._hovered = True
        self._redraw()

    def _on_leave(self, _event=None):
        self._hovered = False
        self._pressed = False
        self._redraw()

    def _on_press(self, _event=None):
        if self._state != "disabled":
            self._pressed = True
            self._redraw()

    def _on_release(self, _event=None):
        if self._state == "disabled":
            return
        was_pressed = self._pressed
        self._pressed = False
        self._redraw()
        if was_pressed and self._command:
            self.after_idle(self._command)

    def config(self, cnf=None, **kwargs):
        if isinstance(cnf, dict):
            kwargs.update(cnf)
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self.configure(cursor="arrow" if self._state == "disabled" else "hand2")
        if "text" in kwargs:
            self._text = kwargs.pop("text")
        if kwargs:
            super().config(**kwargs)
        self._redraw()

class DarkEntry(tk.Frame):
    """Flat entry with a clean one-pixel border and no themed corner artwork."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, background=THEME_BORDER, borderwidth=0)
        self.entry = tk.Entry(
            self, background=THEME_INPUT, foreground=THEME_TEXT,
            insertbackground=THEME_TEXT, selectbackground=THEME_ACCENT,
            selectforeground="#ffffff", relief="flat", borderwidth=0,
            highlightthickness=0, font=("Segoe UI", 9), **kwargs
        )
        self.entry.pack(fill="both", expand=True, padx=1, pady=1, ipady=3)
        self.entry.bind("<FocusIn>", lambda _e: self.configure(background=THEME_ACCENT))
        self.entry.bind("<FocusOut>", lambda _e: self.configure(background=THEME_BORDER))

    def bind(self, sequence=None, func=None, add=None):
        return self.entry.bind(sequence, func, add)

    def get(self):
        return self.entry.get()

class DarkCombobox(tk.Frame):
    """Flat combobox with an external border, avoiding Ttk field corner pixels."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, background=THEME_BORDER, borderwidth=0)
        self.combo = ttk.Combobox(self, style="Flat.TCombobox", **kwargs)
        self.combo.pack(fill="both", expand=True, padx=1, pady=1)
        self.combo.bind("<FocusIn>", lambda _e: self.configure(background=THEME_ACCENT))
        self.combo.bind("<FocusOut>", lambda _e: self.configure(background=THEME_BORDER))

    def __getitem__(self, key):
        return self.combo[key]

    def __setitem__(self, key, value):
        self.combo[key] = value

    def current(self, index=None):
        return self.combo.current(index)

    def set(self, value):
        return self.combo.set(value)

    def get(self):
        return self.combo.get()

    def bind(self, sequence=None, func=None, add=None):
        return self.combo.bind(sequence, func, add)

set_windows_app_id()
root = TkinterDnD.Tk()
root.title(APP_WINDOW_TITLE)
root.configure(background=THEME_BG, padx=10, pady=8)
root.minsize(800, 520)

root.option_add("*Font", ("Segoe UI", 9))
root.option_add("*Label.Background", THEME_BG)
root.option_add("*Label.Foreground", THEME_TEXT)
root.option_add("*Frame.Background", THEME_BG)
root.option_add("*Checkbutton.Background", THEME_BG)
root.option_add("*Checkbutton.Foreground", THEME_TEXT)
root.option_add("*Checkbutton.ActiveBackground", THEME_BG)
root.option_add("*Checkbutton.ActiveForeground", THEME_TEXT)
root.option_add("*Checkbutton.SelectColor", THEME_INPUT)
root.option_add("*Entry.Background", THEME_INPUT)
root.option_add("*Entry.Foreground", THEME_TEXT)
root.option_add("*Entry.InsertBackground", THEME_TEXT)
root.option_add("*Entry.Relief", "flat")
root.option_add("*Entry.HighlightThickness", 0)
root.option_add("*Text.Background", THEME_SURFACE)
root.option_add("*Text.Foreground", THEME_TEXT)
root.option_add("*Text.InsertBackground", THEME_TEXT)
root.option_add("*TCombobox*Listbox.background", THEME_INPUT)
root.option_add("*TCombobox*Listbox.foreground", THEME_TEXT)
root.option_add("*TCombobox*Listbox.selectBackground", THEME_ACCENT)

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TCombobox", fieldbackground=THEME_INPUT, background=THEME_INPUT,
                foreground=THEME_TEXT, arrowcolor=THEME_MUTED,
                bordercolor=THEME_INPUT, lightcolor=THEME_INPUT,
                darkcolor=THEME_INPUT, focuscolor=THEME_INPUT,
                relief="flat", borderwidth=0, padding=3)
style.map("TCombobox",
          fieldbackground=[("readonly", THEME_INPUT)],
          background=[("active", THEME_INPUT), ("pressed", THEME_INPUT),
                      ("readonly", THEME_INPUT)],
          foreground=[("readonly", THEME_TEXT)],
          selectbackground=[("readonly", THEME_INPUT)],
          selectforeground=[("readonly", THEME_TEXT)],
          bordercolor=[("focus", THEME_INPUT), ("active", THEME_INPUT)],
          lightcolor=[("focus", THEME_INPUT), ("active", THEME_INPUT)],
          darkcolor=[("focus", THEME_INPUT), ("active", THEME_INPUT)])
style.layout("Flat.TCombobox", [
    ("Combobox.downarrow", {"side": "right", "sticky": "ns"}),
    ("Combobox.padding", {
        "expand": "1", "sticky": "nswe",
        "children": [("Combobox.textarea", {"sticky": "nswe"})]
    }),
])
style.configure("Flat.TCombobox", fieldbackground=THEME_INPUT,
                background=THEME_INPUT, foreground=THEME_TEXT,
                arrowcolor=THEME_MUTED, borderwidth=0, relief="flat", padding=2)
style.map("Flat.TCombobox",
          fieldbackground=[("readonly", THEME_INPUT), ("focus", THEME_INPUT)],
          background=[("readonly", THEME_INPUT), ("active", THEME_INPUT),
                      ("pressed", THEME_INPUT)],
          foreground=[("readonly", THEME_TEXT)],
          selectbackground=[("readonly", THEME_INPUT)],
          selectforeground=[("readonly", THEME_TEXT)],
          arrowcolor=[("active", THEME_TEXT), ("pressed", THEME_TEXT)])
style.configure("TEntry", fieldbackground=THEME_INPUT, foreground=THEME_TEXT,
                insertcolor=THEME_TEXT, bordercolor=THEME_INPUT,
                lightcolor=THEME_INPUT, darkcolor=THEME_INPUT,
                focuscolor=THEME_INPUT, relief="flat", borderwidth=0, padding=4)
style.map("TEntry",
          fieldbackground=[("focus", THEME_INPUT), ("active", THEME_INPUT)],
          bordercolor=[("focus", THEME_INPUT), ("active", THEME_INPUT)],
          lightcolor=[("focus", THEME_INPUT), ("active", THEME_INPUT)],
          darkcolor=[("focus", THEME_INPUT), ("active", THEME_INPUT)])
style.configure("TCheckbutton", background=THEME_BG, foreground=THEME_TEXT,
                indicatorcolor=THEME_INPUT, indicatorrelief="flat", padding=1)
style.map("TCheckbutton", background=[("active", THEME_BG)],
          foreground=[("active", THEME_TEXT)],
          indicatorcolor=[("selected", THEME_ACCENT)])
style.configure("Horizontal.TProgressbar", background=THEME_ACCENT,
                troughcolor=THEME_SURFACE, bordercolor=THEME_SURFACE,
                lightcolor=THEME_ACCENT, darkcolor=THEME_ACCENT, thickness=8)
if os.path.exists(APP_ICON):
    try:
        root.iconbitmap(default=APP_ICON)
    except Exception:
        pass

# Configure columns
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=0)
root.rowconfigure(13, weight=1)

vid1_var = tk.StringVar()
vid2_var = tk.StringVar()
output_video_var = tk.StringVar()
output_path_state = {"custom": False}
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
fast_mode_var = tk.BooleanVar(value=False)
ui_language_var = tk.StringVar(value="en")
status_var = tk.StringVar(value=tr("ready"))
progress_var = tk.DoubleVar(value=0)

ui_text_widgets = []

def localized_widget(widget, key):
    ui_text_widgets.append((widget, key))
    widget.config(text=tr(key))
    return widget

def refresh_ui_language(*_):
    global _active_ui_language
    _active_ui_language = ui_language_var.get() or "en"
    for widget, key in ui_text_widgets:
        widget.config(text=tr(key))
    if status_var.get() in {TRANSLATIONS["en"]["ready"], TRANSLATIONS["el"]["ready"]}:
        status_var.set(tr("ready"))

_load_default_settings_on_startup()
refresh_ui_language()
ui_language_var.trace_add("write", refresh_ui_language)

# Source video row with frame
localized_widget(tk.Label(root), "source_video").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=3)
source_frame = tk.Frame(root)
source_frame.grid(row=0, column=1, columnspan=2, sticky="ew", padx=2, pady=3)
source_frame.columnconfigure(0, weight=1)
DarkEntry(source_frame, textvariable=vid1_var).grid(row=0, column=0, sticky="ew")
localized_widget(ShadowButton(source_frame, text="", command=browse_source, width=92, height=28), "browse").grid(row=0, column=1, sticky="e", padx=(6, 0))

# Source Audio Track Selection
localized_widget(tk.Label(root), "source_track").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=3)
source_audio_frame = tk.Frame(root)
source_audio_frame.grid(row=1, column=1, columnspan=2, sticky="ew", padx=2, pady=3)
source_audio_frame.columnconfigure(0, weight=1)
cb_audio_tracks = DarkCombobox(source_audio_frame, textvariable=source_audio_track_var, state="readonly")
cb_audio_tracks.grid(row=0, column=0, sticky="ew", padx=(0, 5))

# Target video row with frame
localized_widget(tk.Label(root), "target_video").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=3)
target_frame = tk.Frame(root)
target_frame.grid(row=2, column=1, columnspan=2, sticky="ew", padx=2, pady=3)
target_frame.columnconfigure(0, weight=1)
DarkEntry(target_frame, textvariable=vid2_var).grid(row=0, column=0, sticky="ew")
localized_widget(ShadowButton(target_frame, text="", command=browse_target, width=92, height=28), "browse").grid(row=0, column=1, sticky="e", padx=(6, 0))

# Audio options
localized_widget(tk.Label(root), "audio_format").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=3)
DarkCombobox(root, textvariable=audio_format_var, values=["mp3", "aac", "opus"], state="readonly").grid(row=3, column=1, sticky="w", padx=2, pady=3)

localized_widget(tk.Label(root), "bitrate").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=3)
DarkCombobox(root, textvariable=bitrate_var, values=["128k","192k","256k","320k"], state="readonly").grid(row=4, column=1, sticky="w", padx=2, pady=3)

# Volume Boost
vol_frame = tk.Frame(root)
vol_frame.grid(row=4, column=2, sticky="w", padx=5, pady=3)
localized_widget(tk.Label(vol_frame), "volume_boost").pack(side="left")
vol_values = ["-20", "-15", "-12", "-10", "-9", "-6", "-5", "-4", "-3", "-2", "-1", "0", "1", "2", "3", "4", "5", "6", "9", "10", "12", "15", "20"]
DarkCombobox(vol_frame, textvariable=volume_boost_var, values=vol_values, width=5).pack(side="left", padx=2)

localized_widget(tk.Label(root), "sample_rate").grid(row=5, column=0, sticky="w", padx=(0, 10), pady=3)
DarkCombobox(root, textvariable=sample_rate_var, values=["44100","48000"], state="readonly").grid(row=5, column=1, sticky="w", padx=2, pady=3)

# Audio language
localized_widget(tk.Label(root), "audio_language").grid(row=6, column=0, sticky="w", padx=(0, 10), pady=3)
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
lang_search_var = tk.StringVar()
lang_frame = tk.Frame(root)
lang_frame.grid(row=6, column=1, sticky="ew", padx=2, pady=3)
lang_frame.columnconfigure(0, weight=0)
lang_frame.columnconfigure(1, weight=1)
localized_widget(tk.Label(lang_frame), "search_language").grid(row=0, column=0, sticky="w", padx=(0, 6))
lang_search_entry = DarkEntry(lang_frame, textvariable=lang_search_var)
lang_search_entry.grid(row=0, column=1, sticky="ew")
cb_lang = DarkCombobox(lang_frame, textvariable=lang_var, values=languages, state="readonly")
cb_lang.grid(row=1, column=0, columnspan=2, sticky="ew")

def _update_language_filter(*_):
    q = (lang_search_var.get() or "").strip().lower()
    if not q:
        filtered = languages
    else:
        filtered = [x for x in languages if q in x.lower()]
    cb_lang["values"] = filtered
    if filtered and lang_var.get() not in filtered:
        lang_var.set(filtered[0])

lang_search_var.trace_add("write", _update_language_filter)
_update_language_filter()
_lang_search = {"buf": "", "after": None}
def _reset_lang_search():
    _lang_search["buf"] = ""
    _lang_search["after"] = None
def _on_lang_keypress(event):
    ks = getattr(event, "keysym", "") or ""
    if ks in {"Up", "Down", "Prior", "Next", "Home", "End", "Left", "Right"}:
        return
    if ks == "BackSpace":
        _lang_search["buf"] = ""
        return "break"
    ch = getattr(event, "char", "") or ""
    if not ch.strip():
        return
    _lang_search["buf"] += ch.lower()
    if _lang_search["after"] is not None:
        try:
            root.after_cancel(_lang_search["after"])
        except Exception:
            pass
    _lang_search["after"] = root.after(900, _reset_lang_search)
    prefix = _lang_search["buf"]
    for item in languages:
        if item.lower().startswith(prefix):
            lang_var.set(item)
            try:
                cb_lang.current(languages.index(item))
            except Exception:
                cb_lang.set(item)
            break
    return "break"
cb_lang.bind("<KeyPress>", _on_lang_keypress)

# Mux options frame
mux_frame = tk.Frame(root)
mux_frame.grid(row=6, column=2, sticky="e", padx=5, pady=3)
localized_widget(ttk.Checkbutton(mux_frame, variable=mux_var), "mux_audio").pack(side="left")
localized_widget(ttk.Checkbutton(mux_frame, variable=set_default_var), "set_default").pack(side="left", padx=5)
localized_widget(ttk.Checkbutton(mux_frame, variable=keep_original_var), "keep_tracks").pack(side="left", padx=5)

# Audio delay input
localized_widget(tk.Label(root), "audio_delay").grid(row=7, column=0, sticky="w", padx=(0, 10), pady=3)
DarkEntry(root, textvariable=audio_delay_var, width=18).grid(row=7, column=1, sticky="w", padx=2, pady=3)

# Stretch options frame
stretch_frame = tk.Frame(root)
stretch_frame.grid(row=7, column=2, sticky="w", padx=5, pady=3)

# Stretch duration checkbox
localized_widget(ttk.Checkbutton(stretch_frame, variable=stretch_duration_var),
                 "stretch_duration").pack(side="left")

# Fast mode checkbox
localized_widget(ttk.Checkbutton(stretch_frame, variable=fast_mode_var),
                 "fast_mode").pack(side="left", padx=5)

# Drag & drop area
localized_widget(tk.Label(root), "output_video").grid(row=8, column=0, sticky="w", padx=(0, 10), pady=3)
output_frame = tk.Frame(root)
output_frame.grid(row=8, column=1, columnspan=2, sticky="ew", padx=2, pady=3)
output_frame.columnconfigure(0, weight=1)
output_entry = DarkEntry(output_frame, textvariable=output_video_var)
output_entry.grid(row=0, column=0, sticky="ew")
output_entry.bind("<KeyRelease>", mark_output_path_custom)
localized_widget(ShadowButton(output_frame, text="", command=browse_output_video, width=92, height=28), "browse").grid(row=0, column=1, padx=6)
localized_widget(ShadowButton(output_frame, text="", command=use_auto_output_path, width=72, height=28,
             color="#35445c", hover_color="#465a78"), "auto").grid(row=0, column=2)

# Keep an automatic path current until the user types or browses to a custom path.
lang_var.trace_add("write", lambda *_: root.after_idle(refresh_auto_output_path))
keep_original_var.trace_add("write", lambda *_: root.after_idle(refresh_auto_output_path))
mux_var.trace_add("write", lambda *_: root.after_idle(refresh_auto_output_path))
source_audio_track_var.trace_add("write", lambda *_: root.after_idle(refresh_auto_output_path))

# Drag & drop area
drop = localized_widget(tk.Label(root,
                background=THEME_SURFACE, foreground=THEME_MUTED,
                relief="flat", highlightthickness=1,
                highlightbackground=THEME_BORDER, height=2,
                font=("Segoe UI Semibold", 9)), "drop_files")
drop.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(6, 3))
drop.drop_target_register(DND_FILES) # type: ignore
drop.dnd_bind("<<Drop>>", on_drop) # type: ignore

# Start/Stop buttons
btn_frame = tk.Frame(root)
btn_frame.grid(row=10, column=0, columnspan=3, pady=6, sticky="ew", padx=5)
btn_frame.columnconfigure(0, weight=1)
btn_frame.columnconfigure(1, weight=1)

btn_start = localized_widget(ShadowButton(btn_frame, text="", command=start_processing,
                         height=34, color=THEME_ACCENT,
                         hover_color=THEME_ACCENT_HOVER), "start_processing")
btn_start.grid(row=0, column=0, sticky="ew", padx=(0, 5))

btn_stop = localized_widget(ShadowButton(btn_frame, text="", command=stop_processing,
                        height=34, color=THEME_DANGER,
                        hover_color=THEME_DANGER_HOVER, state="disabled"), "stop_processing")
btn_stop.grid(row=0, column=1, sticky="ew", padx=(5, 0))

settings_frame = tk.Frame(btn_frame)
settings_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
localized_widget(ShadowButton(settings_frame, text="", command=save_default_settings,
             width=126, height=27, color="#263247", hover_color="#35445e"), "save_default").pack(side="left", padx=(0, 3))
localized_widget(ShadowButton(settings_frame, text="", command=load_default_settings,
             width=126, height=27, color="#263247", hover_color="#35445e"), "load_default").pack(side="left", padx=3)
localized_widget(ShadowButton(settings_frame, text="", command=save_settings_as,
             width=100, height=27, color="#263247", hover_color="#35445e"), "save_as").pack(side="left", padx=3)
localized_widget(ShadowButton(settings_frame, text="", command=load_settings_from,
             width=100, height=27, color="#263247", hover_color="#35445e"), "load_from").pack(side="left", padx=3)
localized_widget(ShadowButton(settings_frame, text="", command=reset_settings_to_initial,
             width=82, height=27, color="#263247", hover_color="#35445e"), "reset").pack(side="left", padx=3)

language_frame = tk.Frame(settings_frame)
language_frame.pack(side="right")
localized_widget(tk.Label(language_frame), "interface_language").pack(side="left", padx=(8, 4))
ui_language_display_var = tk.StringVar(value=tr("greek") if ui_language_var.get() == "el" else tr("english"))
ui_language_combo = DarkCombobox(language_frame, textvariable=ui_language_display_var,
                                 values=[tr("english"), tr("greek")], state="readonly", width=10)
ui_language_combo.pack(side="left")

def change_interface_language(*_):
    ui_language_var.set("el" if ui_language_display_var.get() == TRANSLATIONS["el"]["greek"] else "en")

ui_language_display_var.trace_add("write", change_interface_language)

# Status and Progress
tk.Label(root, textvariable=status_var, foreground=THEME_MUTED).grid(row=11, column=0, columnspan=3, sticky="w", pady=(6, 2))
ttk.Progressbar(root, variable=progress_var, maximum=100).grid(row=12, column=0, columnspan=3, sticky="ew", padx=5, pady=2)

# Log panel. The scrollbar stays hidden until the content exceeds the viewport.
log_frame = tk.Frame(root, background=THEME_SURFACE)
log_frame.grid(row=13, column=0, columnspan=3, sticky="nsew", pady=(6, 0))
log_frame.rowconfigure(0, weight=1)
log_frame.columnconfigure(0, weight=1)
log_box = tk.Text(log_frame, height=6, background=THEME_SURFACE,
                  foreground=THEME_TEXT, insertbackground=THEME_TEXT,
                  selectbackground=THEME_ACCENT, relief="flat",
                  borderwidth=0, padx=8, pady=6,
                  font=("Cascadia Mono", 9))
log_box.grid(row=0, column=0, sticky="nsew")
log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_box.yview)

def update_log_scrollbar(first, last):
    log_scrollbar.set(first, last)
    if float(first) > 0.0 or float(last) < 1.0:
        log_scrollbar.grid(row=0, column=1, sticky="ns")
    else:
        log_scrollbar.grid_remove()

log_box.configure(yscrollcommand=update_log_scrollbar)
log_box.config(state="disabled")

def _drain_ui_queue():
    while True:
        try:
            callback, args, kwargs = ui_queue.get_nowait()
        except queue.Empty:
            break
        try:
            callback(*args, **kwargs)
        except tk.TclError:
            return
    root.after(50, _drain_ui_queue)

def _windows_colorref(hex_color):
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return red | (green << 8) | (blue << 16)

def set_dark_titlebar():
    if os.name != "nt":
        return
    try:
        root.update_idletasks()
        widget_handle = root.winfo_id()
        ctypes.windll.user32.GetParent.restype = ctypes.c_void_p
        parent_handle = ctypes.windll.user32.GetParent(widget_handle)
        handles = [handle for handle in (parent_handle, widget_handle) if handle]
        dwm = ctypes.windll.dwmapi

        dark_mode = ctypes.c_int(1)
        caption = ctypes.c_int(_windows_colorref(THEME_BG))
        border = ctypes.c_int(_windows_colorref(THEME_BORDER))
        title_text = ctypes.c_int(_windows_colorref(THEME_TEXT))

        for handle in handles:
            # Attribute 20 is current Windows 10/11; 19 supports older builds.
            for attribute in (20, 19):
                dwm.DwmSetWindowAttribute(
                    handle, attribute, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode)
                )
            # Windows 11 caption, border, and title-text colors.
            for attribute, value in ((35, caption), (34, border), (36, title_text)):
                dwm.DwmSetWindowAttribute(
                    handle, attribute, ctypes.byref(value), ctypes.sizeof(value)
                )
    except Exception:
        pass

def center_window():
    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()
    x = max(0, (root.winfo_screenwidth() - width) // 2)
    y = max(0, (root.winfo_screenheight() - height) // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

center_window()
set_dark_titlebar()
root.after(100, set_dark_titlebar)
root.after(50, _drain_ui_queue)
root.mainloop()
