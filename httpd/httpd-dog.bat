:: Check and kill httpd.exe if it's memory large the 100M.

@echo off
SETLOCAL

pushd %~dp0..\..
set __ROOT=%cd%
set __HTTPD_PATH=%__ROOT%\PortableTrac\httpd\Apache2.2
set __PATH_COND=%__HTTPD_PATH:\=\\%

:: The query is XXX LIKE '%XXX%', to use environment variable, we should use LIKE '%%%ENV_VAR%%%'
:: And to use it as the argument of batch file, the final format should be '%%%%%ENV_VAR%%%%%'
set __COND_LIST=where "name='httpd.exe' and commandLine LIKE '%%%%%__PATH_COND%%%%%'"
set __COND=where "name='httpd.exe' and commandLine LIKE '%%%%%__PATH_COND%%%%%' and workingsetsize>100000000"

:REDO
    call "%__ROOT%\AdminShells\.includes\timestamp.bat"
    set _LOG=%__HTTPD_PATH%\logs\dog-%TIMESTAMP_DATE%.log
    echo %DATE% %TIME% >> "%_LOG%"
    call "%__ROOT%\AdminShells\wmic\wmic-ascii.bat" process %__COND_LIST% get CommandLine,CreationDate,KernelModeTime,PeakVirtualSize,PeakWorkingSetSize,ThreadCount,VirtualSize,WorkingSetSize >> "%_LOG%"
    call "%__ROOT%\AdminShells\wmic\wmic-ascii.bat" process %__COND% call terminate >> "%_LOG%"
    ping 127.0.0.1 -n 120 > nul
GOTO REDO

ENDLOCAL