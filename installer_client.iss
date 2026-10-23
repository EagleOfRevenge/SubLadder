; SubLadder client installer (Inno Setup)
#define MyAppName "Sub Ladder"
#define MyAppVersion "Closed Beta 2"
#define MyAppPublisher "Sub Ladder"
#define MyAppExeName "SubLadder.exe"
#define MySourceDir "dist\\SubLadder-Installer"

[Setup]
AppId={{9C0B4F6A-6A06-4FB7-B5CF-3BFA3E0F8C91}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\\Sub Ladder
DefaultGroupName=Sub Ladder
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=SubLadder-Client-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MySourceDir}\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\\Sub Ladder"; Filename: "{app}\\{#MyAppExeName}"
Name: "{autodesktop}\\Sub Ladder"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "Launch Sub Ladder"; Flags: nowait postinstall skipifsilent
