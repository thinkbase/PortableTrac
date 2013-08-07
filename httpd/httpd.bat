@echo off

SETLOCAL

echo.
echo ---^> Start httpd:
echo .     - started in "%CD%"
echo.
echo ---^> PATH: %PATH%
@echo on
call "%PORTABLE_HOME%\httpd\Apache2.2\bin\httpd.exe"
@echo off

ENDLOCAL