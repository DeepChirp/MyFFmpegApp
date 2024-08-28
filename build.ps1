Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)
pyinstaller --clean --noconfirm MyFFmpegApp.spec