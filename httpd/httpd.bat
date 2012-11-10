@echo off

SETLOCAL

set VIRTUAL_DISK=B
subst %VIRTUAL_DISK%: /D > NUL
subst %VIRTUAL_DISK%: "%PORTABLE_HOME%\httpd"

@echo on
call "%PORTABLE_HOME%\httpd\Apache2.2\bin\httpd.exe"
@echo off

subst %VIRTUAL_DISK%: /D

ENDLOCAL