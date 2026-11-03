; Inno Setup script for tkinterFit
; Build the PyInstaller bundle first (see build.ps1), then compile this with:
;   ISCC.exe installer\tkinterFit.iss
; The resulting installer is written to installer\Output\

#define MyAppName "tkinterFit"
#define MyAppVersion "1.4.0"
#define MyAppPublisher "Ross Moffett"
#define MyAppContact "findcurves@gmail.com"
#define MyAppExeName "tkinterFit.exe"

[Setup]
; AppId uniquely identifies this application - do not change it between versions
AppId={{6C1E6F2B-3A5D-4E8B-9C2A-7F1D4B8E2A61}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact={#MyAppContact}
AppCopyright=Copyright (C) 2016 James R. Phillips, (C) 2026 Ross Moffett
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt
OutputDir=Output
OutputBaseFilename=tkinterFit-{#MyAppVersion}-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; install per-user by default (no admin rights needed); users may choose all-users
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\tkinterFit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
