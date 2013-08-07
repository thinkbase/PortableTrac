@echo off

SETLOCAL

set ENV=%1
IF NOT DEFINED ENV (
    echo.
    echo Error: 1st argument[trac environment] missing.
    exit /b -10
)

set COPY_SOURCE=%TRACENV%\..\backup\%ENV%

IF NOT EXIST "%COPY_SOURCE%\" (
    echo.
    echo Error: backup folder [%COPY_SOURCE%] not found.
    exit /b -20
)
IF EXIST "%COPY_SOURCE%\" (
    IF EXIST "%TRACENV%\%ENV%\" (
        echo.
        echo Error: trac environment [%TRACENV%\%ENV%] already exists.
        exit /b -21
    )
)

@echo on
xcopy /E /H "%COPY_SOURCE%" "%TRACENV%\%ENV%\"
del "%TRACENV%\%ENV%\db\trac.db"
"%SQLITE_HOME%\sqlite3.exe" "%TRACENV%\%ENV%\db\trac.db" < "%TRACENV%\%ENV%\trac-db.sql"

:: Do hook - after-restore-sql
set HOOK_PROG_AFTER_RESTORE_SQL=%COPY_SOURCE%\thinkbase.net\after-restore-sql.bat
set FILE_AFTER_RESTORE_SQL=%TEMP%\%ENV%_%time::=-%_after-restore.sql
set FILE_AFTER_RESTORE_SQL=%FILE_AFTER_RESTORE_SQL: =_%
del /F/Q "%FILE_AFTER_RESTORE_SQL%"
IF EXIST "%HOOK_PROG_AFTER_RESTORE_SQL%" (
    call "%HOOK_PROG_AFTER_RESTORE_SQL%" "%FILE_AFTER_RESTORE_SQL%"
    "%SQLITE_HOME%\sqlite3.exe" "%TRACENV%\%ENV%\db\trac.db" < "%FILE_AFTER_RESTORE_SQL%"
)

@echo off

ENDLOCAL