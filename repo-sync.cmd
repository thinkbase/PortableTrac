@echo off

SETLOCAL
cd /d %~dp0%
call bin\init-env.bat

pushd "%SITE_BASE%\tracenv"
for /d %%i in (*) do (
     if [%%i] neq [.egg-cache] call "%PORTABLE_HOME%\trac-admin" %%i repository sync *
)
popd

ENDLOCAL