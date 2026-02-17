# FPS-Audio-Sync-Tool
Sync audio between different FPS video files and Codecs, preserves original audio tracks and set new audio as default. 

Requires ffmpeg.exe and ffprobe.exe in root folder.

<img width="653" height="586" alt="εικόνα" src="https://github.com/user-attachments/assets/e76a33c4-7ce7-4dee-ace9-9b08130aa189" />

You can use this command to compile it to exe file:
python -m PyInstaller --onefile --windowed --clean --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --hidden-import=tkinterdnd2 fps_audio_sync_ui.py
