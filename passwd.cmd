@echo off

SETLOCAL
cd /d %~dp0%
call bin\init-env.bat

set FILE=%TRACENV%\..\protected\passwd
set USER=%1
set PASS=%2

@echo on
call python.exe bin\trac-digest.py -u %USER% -p %PASS% >> %FILE%
@echo off

ENDLOCAL