:: Import Windows Registry for portable python
:: Many python modules' windows installation program need the registry entry
@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

pushd %~dp0..
set _PWD=%cd%
for  /d  %%i  in (*Portable*Python*2.7*)  do (
    set _PY_=%_PWD%\%%i
    echo Find python 2.7 at: %_PWD%\!_PY_!
    echo.
    
    :: Create register file
    set _REG_="%TEMP%\import-%%i.reg"
    echo Windows Registry Editor Version 5.00 > !_REG_!
    echo [HKEY_CURRENT_USER\Software\Python] >> !_REG_!
    echo [HKEY_CURRENT_USER\Software\Python\PythonCore] >> !_REG_!
    echo [HKEY_CURRENT_USER\Software\Python\PythonCore\2.7] >> !_REG_!
    echo [HKEY_CURRENT_USER\Software\Python\PythonCore\2.7\InstallPath] >> !_REG_!
    echo @="!_PY_:\=\\!\\App" >> !_REG_!
    
    echo Register file !_REG_! should be imported ...
    echo.
    type !_REG_!
    echo.
    regedit /s !_REG_!
    echo Register file !_REG_! has been imported .
    echo.
    pause
    
    :: Finish when first python 2.7 found
    popd
    exit /b 0
)
echo *** Can't find Portable Python 2.7 directory ***
echo .   Registry can't be imported.
echo.
pause

popd
exit /b -1

ENDLOCAL