# FPS-Audio-Sync-Tool v1.9
Sync audio between different FPS video files and Codecs, preserves original audio tracks and set new audio as default. 

Requires ffmpeg.exe and ffprobe.exe in root folder.

<b>v1.9</b></br>
• Added Stop Process button.</br>
• Added Total time elapsed.</br>
• Added avg_frame_rate for more accurent FPS detection.</br>

<b>v1.8</b></br>
• Added Elapsed time and remaning time.</br>
	
<b>v1.7</b></br>
• Optimizing Audio Encoding implemented the "Fast Mode" which simply resamples audio instead of time-stretching, offering a significant speed boost at the cost of pitch shift. I also added support for filter multi-threading.
		
<b>v1.6</b></br>
• Optimized the audio encoding process. It now uses a single FFmpeg pass with multi-threading, which should significantly improve speed and resource usage.

  
<img width="653" height="586" alt="εικόνα" src="https://github.com/user-attachments/assets/e76a33c4-7ce7-4dee-ace9-9b08130aa189" />

You can use this command to compile it to exe file:
python -m PyInstaller --onefile --windowed --clean --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --hidden-import=tkinterdnd2 fps_audio_sync_ui.py
