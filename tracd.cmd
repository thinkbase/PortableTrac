@echo off

SETLOCAL
cd /d %~dp0%
call bin\init-env.bat

set WINPDB_RPDB2=
IF [%1]==[DEBUG] (
	set WINPDB_RPDB2=bin\winpdb-1.4.8\rpdb2.py -d -r
	shift
)

set PORT=%1
set PRJ=%TRACENV%\%2
set AUTH=*,%TRACENV%\..\protected\passwd,trac

@echo on
@title Trac: %2
call python.exe %WINPDB_RPDB2% "%TRAC_INSTALL_PATH%\Scripts\tracd-script.py" -p %1 --auth="%AUTH%" "%PRJ%"
@echo off

ENDLOCAL