# FPS Audio Sync Tool

A Windows utility for synchronizing audio between videos with different frame
rates or durations. It can also process a selected audio track without a target
video, adjust its volume or delay, and mux it back into the source video.

![FPS Audio Sync Tool](Screenshot_1.png)

## Features

- Synchronize audio using source and target FPS
- Stretch audio to the target video's exact duration
- Fast pitch-shift mode for quicker processing
- Positive and negative audio delay
- Volume adjustment from -20 dB to +20 dB
- AAC, MP3, and Opus output
- Select a specific source audio track
- Preserve or remove existing audio tracks
- Set the processed track as the default
- Search audio languages and write language metadata
- Switch the interface live between English and Greek
- Save and load processing profiles
- Drag-and-drop video loading
- Progress, elapsed-time, and remaining-time display
- Start and Stop controls with reliable process cancellation
- Select a custom output video path or use automatic target/source-folder output
- Include all resulting audio languages in generated filenames (for example, `_EN-GR.mkv`)
- Modern black interface with shadowed, interactive controls

## Download

Download the newest standalone Windows executable from the
[latest release](../../releases/latest). Keep the supplied `tools` folder beside
the executable. The application looks for `tools\ffmpeg.exe` and
`tools\ffprobe.exe` first, then falls back to tools placed directly beside the
application.

## How to use

1. Select the source video containing the audio you want to process.
2. Select its audio track.
3. Optionally select a target video. Leave it empty for source-only processing.
4. Choose the audio format, bitrate, language, delay, and other options.
5. Keep the automatic output path or select a custom output video file.
6. Select **Start Processing**.

The generated audio and optional muxed video are saved beside the source or
target video.

## Run from source

Requirements:

- Python 3
- `tkinterdnd2`
- `ffmpeg.exe` and `ffprobe.exe` in the project folder

```powershell
python -m pip install tkinterdnd2
python fps_audio_sync_ui.py
```

## Build the Windows executable

Install the build dependencies and run `build.bat`:

```powershell
python -m pip install pyinstaller tkinterdnd2
build.bat
```

The executable is created in the `dist` folder, and the build script copies
FFmpeg and FFprobe into `dist\tools` as separate files.

## Current version

Version 2.5 adds live English/Greek interface switching, remembers the selected
interface language in settings profiles, standardizes form-field spacing, and
shows a vertical event-log scrollbar automatically when the log becomes full.
See [changelog.txt](changelog.txt) for the full version history.
