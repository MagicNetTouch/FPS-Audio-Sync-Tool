# FPS-Audio-Sync-Tool v2.3
Sync audio between different FPS video files and Codecs, preserves original audio tracks and set new audio as default. 

Requires <b>ffmpeg.exe</b> and <b>ffprobe.exe</b> in root folder.

<b>v2.2</b></br>
• Added Audio language Search</br>
• Added Profile Save/Load</br>

<b>v2.2</b></br>
• Added better compatibility on audio track language metadata writing on output video</br>
• Added option to keep or not original audio tracks</br>
• Added ability to volume boost source's specific audio track without the need of whole process and target video</br>
	
<b>v2.1</b></br>
• Added Volume Boost.</br>

<b>v2.0</b></br>
• Added Opus Audio format.</br>

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



You can use this command to compile it to exe file:
python -m PyInstaller --onefile --windowed --clean --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --hidden-import=tkinterdnd2 fps_audio_sync_ui.py
