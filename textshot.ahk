#NoEnv
SetWorkingDir %A_ScriptDir%
; Bind the script to Win + Alt + S; modify as needed
#!s::
Run, pythonw.exe textshot.py
Return