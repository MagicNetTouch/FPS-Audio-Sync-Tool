@echo off
python -m PyInstaller --clean --noconfirm fps_audio_sync_ui.spec
if errorlevel 1 goto :end

if not exist "dist\tools" mkdir "dist\tools"
copy /Y "ffmpeg.exe" "dist\tools\ffmpeg.exe"
copy /Y "ffprobe.exe" "dist\tools\ffprobe.exe"

:end
pause
