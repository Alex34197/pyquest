@echo off
REM Crea el INSTALADOR de Windows (dist\PyQuest-Setup-1.1.0.exe) con Inno Setup.
REM Requiere Inno Setup 6 o 7: https://jrsoftware.org/isdl.php
setlocal
cd /d "%~dp0\.."

REM 1) compila la app (one-dir) si hace falta
if not exist "dist\PyQuest\PyQuest.exe" call build\build_windows.bat

REM 2) localiza el compilador de Inno Setup (ISCC.exe)
set "ISCC=ISCC.exe"
where ISCC >nul 2>&1 || (
  if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
  if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
  if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
)
if not exist "%ISCC%" where "%ISCC%" >nul 2>&1 || (
  echo.
  echo  No se encontro Inno Setup. Instalalo desde https://jrsoftware.org/isdl.php
  exit /b 1
)

REM 3) compila el instalador
"%ISCC%" PyQuest.iss || (
  echo.
  echo  Fallo al compilar el instalador.
  exit /b 1
)

echo.
echo  Instalador creado: dist\PyQuest-Setup-1.1.0.exe
echo  (Opcional) firmalo:  build\sign_windows.ps1 -Exe dist\PyQuest-Setup-1.1.0.exe
endlocal
