[Setup]
AppName=Dindigul School Point
AppVersion=1.0.0
AppPublisher=Dindigul School Point
DefaultDirName={autopf}\DindigulSchoolPoint
DefaultGroupName=Dindigul School Point
OutputDir=installer_output
OutputBaseFilename=DindigulSchoolPoint_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\StockManager.exe
UninstallDisplayName=Dindigul School Point

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\StockManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Dindigul School Point"; Filename: "{app}\StockManager.exe"; IconFilename: "{app}\StockManager.exe"
Name: "{group}\Uninstall Dindigul School Point"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Dindigul School Point"; Filename: "{app}\StockManager.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\StockManager.exe"; Description: "Launch Dindigul School Point"; Flags: nowait postinstall skipifsilent shellexec

[Code]

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  MsgResult: Integer;
  Msg: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := 'C:\StockManager';

    if DirExists(DataDir) then
    begin
      Msg := 'Do you want to delete all Dindigul School Point data?';
      Msg := Msg + Chr(13) + Chr(10) + Chr(13) + Chr(10);
      Msg := Msg + 'This will permanently delete all your database, backups, invoices and logs from C:\StockManager';
      Msg := Msg + Chr(13) + Chr(10) + Chr(13) + Chr(10);
      Msg := Msg + 'YES = Delete everything   |   NO = Keep my data';

      MsgResult := MsgBox(Msg, mbConfirmation, MB_YESNO);

      if MsgResult = IDYES then
      begin
        DelTree(DataDir, True, True, True);
        MsgBox('All data has been deleted.', mbInformation, MB_OK);
      end
      else
      begin
        MsgBox('Your data has been kept at: C:\StockManager', mbInformation, MB_OK);
      end;
    end;
  end;
end;