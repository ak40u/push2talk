@echo off
echo [Push2Talk] Installing PyInstaller...
venv\Scripts\pip.exe install pyinstaller
echo.
echo [Push2Talk] Building Push2Talk.exe...
venv\Scripts\pyinstaller.exe push2talk.spec
echo.
if exist dist\Push2Talk.exe (
    echo [Push2Talk] Build complete: dist\Push2Talk.exe
    echo [Push2Talk] NOTE: Manually copy .env and sa-key.json to dist\ before running
) else (
    echo [Push2Talk] Build FAILED. Check output above.
)
pause
