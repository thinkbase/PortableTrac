@echo off
SETLOCAL

pushd %~dp0..

echo ______________________________________________________________________
echo ----------------------------------------------------------------------
echo *** Run default trac environment at http port 8080 ***
echo ----------------------------------------------------------------------
echo.

IF NOT EXIST .\protected\passwd (
    call passwd.cmd admin 111111
    echo ----------------------------------------------------------------------
    echo *** The default administrator's name is [admin], password is [111111] .
    echo ----------------------------------------------------------------------
    echo.
)

echo.
echo *** Now should start the server(tracd), at http port 8080 ...
echo.
pause
call tracd 8080 default

popd

ENDLOCAL