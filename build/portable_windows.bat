@echo off
REM ============================================================
REM  PyQuest PORTABLE: genera UN SOLO archivo independiente.
REM  Doble clic, o ejecuta:  build\portable_windows.bat
REM  Resultado:  dist\PyQuest.exe   (un unico archivo, copialo donde quieras)
REM ============================================================
setlocal
cd /d "%~dp0\.."

python -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

REM limpia restos de una compilacion anterior para no confundir salidas
if exist dist rmdir /s /q dist

pyinstaller --noconfirm PyQuest-onefile.spec

echo.
echo ================================================================
echo   TU ARCHIVO INDEPENDIENTE ES:   dist\PyQuest.exe
echo.
echo   - Copia SOLO ese archivo a otro Windows y funciona tal cual.
echo   - NO uses la carpeta dist\PyQuest\ (esa es la version "carpeta").
echo.
echo   (Opcional) firmarlo con tu nombre:
echo       powershell -ExecutionPolicy Bypass -File build\sign_windows.ps1 -Exe dist\PyQuest.exe
echo ================================================================
pause
endlocal
