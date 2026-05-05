$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Startup') + '\\PrediCare.lnk')
$Shortcut.TargetPath = 'C:\\Users\\user\\Downloads\\preeclampsia tables\\start_predicare.bat'
$Shortcut.WorkingDirectory = 'C:\\Users\\user\\Downloads\\preeclampsia tables'
$Shortcut.Save()
