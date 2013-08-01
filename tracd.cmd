@echo off

SETLOCAL
cd /d %~dp0%
call bin\init-env.bat

set WINPDB_RPDB2=
IF [%1]==[DEBUG] (
	set WINPDB_RPDB2=bin\winpdb-1.4.8\rpdb2.py -d -r
	shift
)

set DIGEST_FILE=%TRACENV%\..\protected\passwd
set AUTH=*,%DIGEST_FILE%,trac

set PORT=%1
IF NOT DEFINED PORT (
    echo.
    echo Error: 1st argument[web server port number] missing.
    exit /b -10
)
set ENV=%2
IF NOT DEFINED ENV (
    echo.
    echo 2nd argument[trac environment] missing, running with ALL environments.
    
    @echo on
    @title Trac
    call python.exe %WINPDB_RPDB2% "%TRAC_INSTALL_PATH%\Scripts\tracd-script.py" -p %1 --auth="%AUTH%" --env-parent-dir %TRACENV%
    @echo off
    
    goto EXIT_POINT
)

set PRJ=%TRACENV%\%ENV%

IF NOT EXIST "%PRJ%\" (
    echo.
    echo Restore trac environment to %PRJ% before start tracd ...
    call bin\do_restore.bat %ENV%
)

IF NOT EXIST "%PRJ%\" (
    echo.
    echo Error: trac environment [%PRJ%] not found.
    exit /b -20
)

IF NOT EXIST "%DIGEST_FILE%" (
    echo.
    echo Error: passwd file missing, please run "passwd admin 111111" to create it.
    exit /b -30
)

@echo on
@title Trac: %2
call python.exe %WINPDB_RPDB2% "%TRAC_INSTALL_PATH%\Scripts\tracd-script.py" -p %1 --auth="%AUTH%" "%PRJ%"
@echo off

:EXIT_POINT
ENDLOCAL