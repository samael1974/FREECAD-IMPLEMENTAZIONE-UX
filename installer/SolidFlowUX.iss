; SolidFlow UX — self-contained Windows installer
; Built with Inno Setup 6. No administrator privileges required.

#define MyAppName "SolidFlow UX"
#define MyAppVersion "0.4.0-beta.10"
#define MyAppPublisher "SolidFlow UX Project"
#define MyAppURL "https://github.com/samael1974/FREECAD-IMPLEMENTAZIONE-UX"

[Setup]
AppId={{B7892BB3-447D-4DF2-AB4E-04665B47DA8D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userappdata}\FreeCAD\v1-1\Mod\SolidFlowUX
DisableDirPage=auto
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=SolidFlowUX-Setup-v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName} {#MyAppVersion}
CreateUninstallRegKey=yes
Uninstallable=yes
CloseApplications=no
RestartApplications=no
SetupLogging=yes

[Files]
; Runtime beta10 only. Historical patch layers stay in GitHub but are not installed.
Source: "..\SolidFlowUX\Init.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\InitGui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_ui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_features.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_smart.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_sketch.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_import.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_viewbar.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_beta5.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_beta6.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_mesh.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_appearance.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_beta7.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\manifest.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\README.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\SolidFlowUX\CHANGELOG.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[InstallDelete]
; Remove historical runtime patch files from older installations.
Type: files; Name: "{app}\solidflow_beta4.py"
Type: files; Name: "{app}\solidflow_beta9.py"
Type: files; Name: "{app}\solidflow_patterns.py"
Type: filesandordirs; Name: "{app}\__pycache__"

[Icons]
Name: "{userprograms}\SolidFlow UX\Apri cartella SolidFlow UX"; Filename: "{app}"
Name: "{userprograms}\SolidFlow UX\Disinstalla SolidFlow UX"; Filename: "{uninstallexe}"

[Code]
function FreeCADIsRunning(): Boolean;
var
  ResultCode: Integer;
  TempFile: String;
begin
  TempFile := ExpandConstant('{tmp}\solidflow_freecad_process.txt');
  Result := False;
  if Exec(ExpandConstant('{cmd}'),
          '/C tasklist /FI "IMAGENAME eq FreeCAD.exe" | find /I "FreeCAD.exe" > "' + TempFile + '"',
          '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Result := (ResultCode = 0);
  end;
  DeleteFile(TempFile);
end;

function InitializeSetup(): Boolean;
begin
  if FreeCADIsRunning() then
  begin
    MsgBox('FreeCAD è aperto.' + #13#10 + #13#10 +
           'Chiudi completamente FreeCAD prima di installare o aggiornare SolidFlow UX.',
           mbError, MB_OK);
    Result := False;
    exit;
  end;
  Result := True;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  LegacyDir, BackupRoot, BackupDir, Stamp: String;
begin
  Result := '';
  LegacyDir := ExpandConstant('{userappdata}\FreeCAD\Mod\SolidFlowUX');
  if not DirExists(LegacyDir) then
    exit;

  Stamp := GetDateTimeString('yyyymmdd_hhnnss', '', '');
  BackupRoot := ExpandConstant('{userappdata}\FreeCAD\SolidFlowUX_Legacy_Backups');
  BackupDir := AddBackslash(BackupRoot) + 'SolidFlowUX_' + Stamp;
  ForceDirectories(BackupRoot);

  if not RenameFile(LegacyDir, BackupDir) then
  begin
    Result := 'È stata trovata una vecchia installazione SolidFlow in:' + #13#10 +
              LegacyDir + #13#10 + #13#10 +
              'Non sono riuscito ad archiviarla automaticamente. ' +
              'Rinomina o sposta quella cartella e ripeti l''installazione per evitare due copie di SolidFlow.';
    exit;
  end;

  MsgBox('La vecchia installazione SolidFlow è stata archiviata in:' + #13#10 +
         BackupDir,
         mbInformation, MB_OK);
end;

procedure BackupExistingInstall();
var
  TargetDir, BackupRoot, BackupDir, Stamp, PSArgs: String;
  ResultCode: Integer;
begin
  TargetDir := ExpandConstant('{app}');
  if not DirExists(TargetDir) then
    exit;

  Stamp := GetDateTimeString('yyyymmdd_hhnnss', '', '');
  BackupRoot := AddBackslash(TargetDir) + '_backup';
  BackupDir := AddBackslash(BackupRoot) + 'installer_' + Stamp;
  ForceDirectories(BackupDir);

  PSArgs := '-NoProfile -ExecutionPolicy Bypass -Command "' +
    '$src=''' + TargetDir + '''; $dst=''' + BackupDir + '''; ' +
    'Get-ChildItem -LiteralPath $src -File | Where-Object {$_.Name -ne ''unins000.exe'' -and $_.Name -ne ''unins000.dat''} | ' +
    'Copy-Item -Destination $dst -Force"';

  Exec('powershell.exe', PSArgs, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  CacheDir: String;
begin
  if CurStep = ssInstall then
    BackupExistingInstall();

  if CurStep = ssPostInstall then
  begin
    CacheDir := AddBackslash(ExpandConstant('{app}')) + '__pycache__';
    if DirExists(CacheDir) then
      DelTree(CacheDir, True, True, True);
  end;
end;

function InitializeUninstall(): Boolean;
begin
  if FreeCADIsRunning() then
  begin
    MsgBox('Chiudi FreeCAD prima di disinstallare SolidFlow UX.', mbError, MB_OK);
    Result := False;
    exit;
  end;
  Result := True;
end;
