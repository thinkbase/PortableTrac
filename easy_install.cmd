@echo off

SETLOCAL
cd /d %~dp0%
call bin\init-env.bat

set PATH=%PATH%;%PYTHONHOME%\Scripts;%PYTHONHOME%

@echo on
call easy_install.exe --prefix="%PORTABLE_HOME%\trac" %*
@echo off

ENDLOCAL