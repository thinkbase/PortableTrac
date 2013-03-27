:: This script should create a sql script file for sqlite to execute after the restore process finished.

:: %1 is the sql file's path, send by caller
IF NOT [%1] EQU [] (
    echo UPDATE repository set value=^'%PORTABLE_HOME%\data\svn-testcase^' WHERE id=^'1^' AND name=^'dir^'^; > "%1"
    echo UPDATE repository set value=^'svn^:42be0d23-f3ec-7742-9214-b333e19b708d^:^'^|^|^'%PORTABLE_HOME:\=/%/data/svn-testcase^' WHERE id=^'1^' AND name=^'repository_dir^'^; >> "%1"
    
    echo SQL Script File is %1
    echo.
    type %1
)
