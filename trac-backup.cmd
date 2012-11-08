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

set COPY_TARGET=%TRACENV%\..\backup\%ENV%
set COPY_TARGET_OLD=%TRACENV%\..\backup\.old\%ENV%.%TIMESTAMP%
IF EXIST "%COPY_TARGET%\" (
    mkdir "%COPY_TARGET_OLD%"
    echo move "%COPY_TARGET%" "%COPY_TARGET_OLD%" ...
    move "%COPY_TARGET%" "%COPY_TARGET_OLD%"
)

@echo on
@title TracBackup: %1
call python.exe %WINPDB_RPDB2% "%TRAC_INSTALL_PATH%\Scripts\trac-admin-script.py" "%TRACENV%\%ENV%" hotcopy "%COPY_TARGET%"
echo .dump | "%SQLITE_HOME%\sqlite3.exe" "%COPY_TARGET%\db\trac.db" > "%COPY_TARGET%\trac-db.sql"
@echo off

ENDLOCAL