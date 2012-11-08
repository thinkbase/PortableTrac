@echo off

SETLOCAL
cd /d %~dp0%
call bin\init-env.bat

set WINPDB_RPDB2=
IF [%1]==[DEBUG] (
	set WINPDB_RPDB2=bin\winpdb-1.4.8\rpdb2.py -d -r
	shift
)

set ENV=%1
IF NOT DEFINED ENV (
    echo.
    echo Error: 1st argument[trac environment] missing.
    exit /b -10
)
set CMD=%2 %3 %4 %5 %6 %7 %8 %9
IF NOT DEFINED CMD (
    echo.
    echo Error: trac admin commands missing.
    exit /b -10
)

@echo on
@title TracAdmin: %1
call python.exe %WINPDB_RPDB2% "%TRAC_INSTALL_PATH%\Scripts\trac-admin-script.py" "%TRACENV%\%ENV%" %CMD%
@echo off

ENDLOCAL