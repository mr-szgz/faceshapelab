; Online setup: only application source and metadata are embedded.
[Setup]
AppId={{B79C28DE-4238-41B3-A058-8896850F7A63}
AppName=FaceShapeLab
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\FaceShapeLab
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0
WizardStyle=modern
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=FaceShapeLab-{#AppVersion}-Setup
Compression=lzma2
SolidCompression=yes
ArchiveExtraction=full
SetupLogging=yes
UninstallDisplayIcon={app}\.venv\Scripts\pythonw.exe

[Files]
Source: "bootstrap.cmd"; Flags: dontcopy
Source: "check_gpu.py"; Flags: dontcopy
Source: "..\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\uv.lock"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\faceshapelab\*.py"; DestDir: "{app}\faceshapelab"; Flags: ignoreversion recursesubdirs
Source: "..\faceshapelab\*.ui"; DestDir: "{app}\faceshapelab"; Flags: ignoreversion recursesubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "launch.pyw"; DestDir: "{app}"; Flags: ignoreversion
Source: "verify_runtime.py"; DestDir: "{app}"; Flags: ignoreversion
#include "..\build\installer\models.iss"

[Icons]
Name: "{autoprograms}\FaceShapeLab"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\launch.pyw"""; WorkingDir: "{userdocs}"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\faceshapelab\__pycache__"
Type: filesandordirs; Name: "{app}\faceshapelab\face_analysis\__pycache__"
Type: filesandordirs; Name: "{app}\faceshapelab\ui\__pycache__"
Type: filesandordirs; Name: "{app}\faceshapelab\ui\core\__pycache__"

[Code]
procedure RunRequired(const Filename, Params, WorkingDir: String);
var
  ResultCode: Integer;
begin
  if not ExecAndLogOutput(Filename, Params, WorkingDir, SW_SHOWNORMAL,
    ewWaitUntilTerminated, ResultCode, nil) then
    RaiseException(SysErrorMessage(ResultCode));
  if ResultCode <> 0 then
    RaiseException(Format('%s exited with code %d. See the Setup log.', [Filename, ResultCode]));
end;

function InitializeSetup: Boolean;
var
  ResultCode: Integer;
begin
  { Use only the explicitly configured toolkit. Never discover or change CUDA. }
  Result := ExecAndLogOutput(GetEnv('CUDA_PATH') + '\bin\nvcc.exe', '--version',
    '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode, nil);
  Result := Result and (ResultCode = 0);
  if not Result then
    Log(Format('CUDA_PATH toolkit check failed with code %d.', [ResultCode]));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  { Exceptions at ssInstall abort Setup, including /VERYSILENT installs. }
  if CurStep = ssInstall then
  begin
    WizardForm.StatusLabel.Caption := 'Downloading the dependency installer...';
    DownloadTemporaryFile('https://github.com/astral-sh/uv/releases/download/0.11.11/uv-x86_64-pc-windows-msvc.zip',
      'uv.zip', '2f75a0db2c3530b6b3c24434dc38137f61ff1f4e5f2d7b4ddc5bcd142cf58b65', nil);
    ExtractArchive(ExpandConstant('{tmp}\uv.zip'), ExpandConstant('{tmp}\tools'), '', True, nil);
    ExtractTemporaryFile('bootstrap.cmd');
    ExtractTemporaryFile('pyproject.toml');
    ExtractTemporaryFile('uv.lock');
    ExtractTemporaryFile('check_gpu.py');
    WizardForm.StatusLabel.Caption := 'Downloading Python and installing locked dependencies...';
    RunRequired(ExpandConstant('{cmd}'), '/D /C ""' + ExpandConstant('{tmp}\bootstrap.cmd') + '" "' + ExpandConstant('{app}') + '""', ExpandConstant('{tmp}'));
    WizardForm.StatusLabel.Caption := 'Checking the installed GPU runtime...';
    RunRequired(ExpandConstant('{app}\.venv\Scripts\python.exe'), '"' + ExpandConstant('{tmp}\check_gpu.py') + '"', ExpandConstant('{tmp}'));
  end;
end;
