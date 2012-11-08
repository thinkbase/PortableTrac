@echo off

SETLOCAL
cd /d %~dp0%
call bin\init-env.bat

@echo on
start pythonw.exe bin\winpdb-1.4.8\winpdb.py
@echo off

ENDLOCAL