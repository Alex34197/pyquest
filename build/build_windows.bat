@echo off
REM Construye PyQuest para Windows.
REM   build_windows.bat           -^> carpeta dist\PyQuest\ (one-dir, mas agil)
REM   build_windows.bat onefile   -^> UN archivo dist\PyQuest.exe (portable)
setlocal
cd /d "%~dp0\.."

set "SPEC=PyQuest.spec"
if /I "%~1"=="onefile" set "SPEC=PyQuest-onefile.spec"

python -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

pyinstaller --noconfirm %SPEC%

REM --- Firma (opcional) ---
REM Firma rapida con certificado autofirmado (solo de confianza en este equipo):
REM     powershell -ExecutionPolicy Bypass -File build\sign_windows.ps1
REM Firma real para distribuir (certificado de una CA): ver SIGNING.md

echo.
echo ================================================================
echo  one-dir:  dist\PyQuest\PyQuest.exe  (copia la CARPETA dist\PyQuest)
echo  onefile:  dist\PyQuest.exe          (UN solo archivo portable)
echo ================================================================
endlocal
