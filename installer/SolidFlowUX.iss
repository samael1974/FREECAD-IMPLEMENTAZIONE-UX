; SolidFlow UX — self-contained Windows installer
; Built with Inno Setup 6. No administrator privileges required.

#define MyAppName "SolidFlow UX"
#define MyAppVersion "0.4.0-beta.13-test.2"
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
DefaultDirName={code:DefaultSolidFlowDir}
DisableDirPage=no
AlwaysShowDirOnReadyPage=yes
AppendDefaultDirName=no
InfoBeforeFile=INSTALLAZIONE.txt
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
; Runtime and standalone installation diagnostics.
Source: "..\SolidFlowUX\Init.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\InitGui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_ui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_features.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_preview.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_inference.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_assisted_line.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_smart.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_sketch.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_import.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_viewbar.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_beta5.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_beta6.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_mesh.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_appearance.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_beta7.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_profiles.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_fillet.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_paths.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_workflows.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_beta12.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\solidflow_diagnostics.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\manifest.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\SolidFlowUX\README.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\SolidFlowUX\CHANGELOG.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "SolidFlowUX-preinstall.ps1"; Flags: dontcopy
Source: "INSTALLAZIONE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\SolidFlowUX-Diagnostica.FCMacro"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
Type: files; Name: "{app}\solidflow_beta4.py"
Type: files; Name: "{app}\solidflow_beta9.py"
Type: files; Name: "{app}\solidflow_patterns.py"
Type: filesandordirs; Name: "{app}\__pycache__"

[Icons]
Name: "{userprograms}\SolidFlow UX\Guida installazione e test"; Filename: "{app}\INSTALLAZIONE.txt"
Name: "{userprograms}\SolidFlow UX\Apri cartella SolidFlow UX"; Filename: "{app}"
Name: "{userprograms}\SolidFlow UX\Disinstalla SolidFlow UX"; Filename: "{uninstallexe}"

[Code]
function DefaultSolidFlowDir(Param: String): String;
var
  DataDir: String;
begin
  DataDir := GetEnv('FREECAD_USER_DATA');
  if (DataDir <> '') and DirExists(DataDir) then
    Result := AddBackslash(DataDir) + 'Mod\SolidFlowUX'
  else
    Result := ExpandConstant('{userappdata}\FreeCAD\v1-1\Mod\SolidFlowUX');
end;

function FreeCADIsRunning(): Boolean;
var
  ResultCode: Integer;
begin
  { Check both GUI and console; no process is forcibly closed. }
  Result := True;
  if Exec(ExpandConstant('{cmd}'),
      '/C tasklist /FI "IMAGENAME eq FreeCAD*" /NH | findstr /I "FreeCAD.exe FreeCADCmd.exe"',
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := (ResultCode <> 1);
end;

function InitializeSetup(): Boolean;
begin
  Result := not FreeCADIsRunning();
  if not Result then
    MsgBox('Chiudi tutte le finestre di FreeCAD prima di installare SolidFlow UX.' + #13#10 +
           'Se FreeCAD è già chiuso, riavvia Windows e riprova.', mbError, MB_OK);
end;

procedure InitializeWizard();
begin
  WizardForm.SelectDirLabel.Caption :=
    'Seleziona la cartella Mod\SolidFlowUX del profilo FreeCAD 1.1 che usi.' + #13#10 +
    'Per versioni portabili o percorsi personalizzati usa la macro di installazione inclusa nel pacchetto tester.';
end;

function ValidTargetDir(): Boolean;
var
  Target: String;
begin
  Target := RemoveBackslashUnlessRoot(ExpandConstant('{app}'));
  Result := (CompareText(ExtractFileName(Target), 'SolidFlowUX') = 0) and
            (CompareText(ExtractFileName(ExtractFileDir(Target)), 'Mod') = 0);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = wpSelectDir) and not ValidTargetDir() then
  begin
    MsgBox('La destinazione deve terminare con Mod\SolidFlowUX.', mbError, MB_OK);
    Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ScriptPath, Params: String;
  ResultCode: Integer;
begin
  Result := '';
  if not ValidTargetDir() then
  begin
    Result := 'Destinazione non valida: seleziona Mod\SolidFlowUX nel tuo profilo FreeCAD.';
    exit;
  end;
  if FreeCADIsRunning() then
  begin
    Result := 'FreeCAD è aperto. Chiudilo e riprova.';
    exit;
  end;
  ExtractTemporaryFile('SolidFlowUX-preinstall.ps1');
  ScriptPath := ExpandConstant('{tmp}\SolidFlowUX-preinstall.ps1');
  Params := '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + ScriptPath +
    '" -TargetDirectory "' + ExpandConstant('{app}') + '"';
  if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := 'Impossibile avviare il controllo e backup. Nessun file runtime è stato sostituito.' + #13#10 +
      'Usa SolidFlowUX-Installa.FCMacro dal pacchetto tester, oppure allega il log del setup alla segnalazione.'
  else if ResultCode <> 0 then
    Result := 'Controllo o backup non riuscito (codice ' + IntToStr(ResultCode) + ').' + #13#10 +
      'Nessun file runtime è stato sostituito. Verifica permessi e spazio disco, oppure usa la macro di installazione.';
end;

function InitializeUninstall(): Boolean;
begin
  Result := not FreeCADIsRunning();
  if not Result then
    MsgBox('Chiudi FreeCAD prima di disinstallare SolidFlow UX.', mbError, MB_OK);
end;
