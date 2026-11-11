; Inno Setup script for FindCurves Studio (formerly tkInterFit)
; Build the PyInstaller bundle first (see build.ps1), then compile this with:
;   ISCC.exe installer\FindCurves.iss
; The resulting installer is written to installer\Output\

#define MyAppName "FindCurves Studio"
#define MyAppVersion "1.4.0"
#define MyAppPublisher "Ross Moffett"
#define MyAppContact "findcurves@gmail.com"
#define MyAppExeName "FindCurves.exe"

[Setup]
; AppId uniquely identifies this application - do not change it between versions.
; It is the same as tkInterFit's, so installing upgrades a tkInterFit installation.
AppId={{6C1E6F2B-3A5D-4E8B-9C2A-7F1D4B8E2A61}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact={#MyAppContact}
AppCopyright=Copyright (C) 2016 James R. Phillips, (C) 2026 Ross Moffett
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.md
OutputDir=Output
OutputBaseFilename=FindCurves-Studio-{#MyAppVersion}-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\icons\FindCurves.ico
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
Source: "..\dist\FindCurves\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; left over from tkInterFit, before it was renamed
Type: files; Name: "{app}\tkinterFit.exe"
Type: files; Name: "{autoprograms}\tkinterFit.lnk"
Type: files; Name: "{autodesktop}\tkinterFit.lnk"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
