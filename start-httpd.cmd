@echo off

:: Kill the running process "httpd.exe" before start it ...
taskkill /f /im httpd.exe

SETLOCAL
cd /d %~dp0%
call bin\init-env.bat

set DIGEST_FILE=%TRACENV%\..\protected\passwd
set AUTH=*,%DIGEST_FILE%,trac

IF NOT EXIST "%DIGEST_FILE%" (
    echo.
    echo Error: passwd file missing, please run "passwd admin 111111" to create it.
    exit /b -30
)

:: Environment variables for trac.wsgi
set TRAC_ENV_PARENT_DIR=%TRACENV%
IF DEFINED SITE_IDX_FILE (
    :: Customize index file, should be abstract path, or be relative to the SITE_BASE
    if exist "%SITE_BASE%\%SITE_IDX_FILE%" (
        set TRAC_ENV_INDEX_TMPL=%SITE_BASE%\%SITE_IDX_FILE%
    )
    if exist "%SITE_IDX_FILE%" (
        set TRAC_ENV_INDEX_TMPL=%SITE_IDX_FILE%
    )
)

@echo on
@title Apache httpd/Trac
:: echo AuthUserFile %TRACENV%\..\protected\passwd > "%PORTABLE_HOME%\httpd\Apache2.2\logs\trac.temp.conf"
call httpd\httpd.bat
@echo off

ENDLOCAL