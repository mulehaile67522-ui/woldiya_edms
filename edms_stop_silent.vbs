' Woldiya EDMS — Silent Auto-Stop
' Kills Django server on shutdown/logoff

Dim shell
Set shell = CreateObject("WScript.Shell")

' Kill by port 8000
shell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :8000') do taskkill /PID %a /F", 0, True

' Kill any manage.py process
shell.Run "cmd /c taskkill /F /FI ""WINDOWTITLE eq ወልድያ EDMS*"" /T", 0, True
shell.Run "cmd /c wmic process where ""name='python.exe' and CommandLine like '%manage.py%'"" delete", 0, True

Set shell = Nothing
