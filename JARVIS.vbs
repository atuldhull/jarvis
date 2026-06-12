' Double-click to start the JARVIS desktop (wallpaper + dock), HIDDEN and DETACHED.
' Because it runs under pythonw with no console and we don't wait on it, closing any
' terminal / VS Code won't stop it — only the dock's OFF button (or Task Manager) will.
Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder  = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = folder
pyw = """" & folder & "\.venv\Scripts\pythonw.exe"""
scr = """" & folder & "\jarvis_desktop.py"""
sh.Run pyw & " " & scr, 0, False   ' window style 0 = hidden, False = don't wait
