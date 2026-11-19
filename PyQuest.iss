; PyQuest.iss — Instalador de Windows (Inno Setup 6).
; PyQuest.iss — Windows installer (Inno Setup 6).
;
; 1) Compila la app one-dir:   build\build_windows.bat   (genera dist\PyQuest\)
; 2) Compila el instalador:     ISCC PyQuest.iss          (o build\make_installer_windows.bat)
; 3) Resultado:                 dist\PyQuest-Setup-1.1.0.exe
;
; Inno Setup (gratis): https://jrsoftware.org/isdl.php

#define AppName "PyQuest"
#define AppVersion "1.1.0"
#define AppPublisher "Alex García González"
#define AppExe "PyQuest.exe"

[Setup]
AppId={{A1F2C3D4-PYQUEST-4E5F-9A8B-0011AABBCCDD}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=dist
OutputBaseFilename=PyQuest-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
DisableProgramGroupPage=yes

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Empaqueta toda la carpeta one-dir generada en dist\PyQuest
Source: "dist\PyQuest\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
