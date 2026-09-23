' Woldiya EDMS — Silent Auto-Start
' Runs Django server with NO visible CMD window

Dim python, project, shell, cmd

python  = "C:\Users\muleh\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe"
project = "C:\Users\muleh\OneDrive\Desktop\woldiya-emds\woldiya_edms"

Set shell = CreateObject("WScript.Shell")

' Step 1: run migrations silently
shell.Run "cmd /c cd /d """ & project & """ && """ & python & """ manage.py migrate --run-syncdb >> """ & project & "\edms_server.log"" 2>&1", 0, True

' Step 2: start server in background (window hidden = 0, don't wait = False)
shell.Run "cmd /c cd /d """ & project & """ && """ & python & """ manage.py runserver 0.0.0.0:8000 >> """ & project & "\edms_server.log"" 2>&1", 0, False

' Step 3: wait 4 seconds then open browser
WScript.Sleep 4000
shell.Run "http://127.0.0.1:8000", 1, False

Set shell = Nothing
