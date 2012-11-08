set _PWD=%~dp0%
:: -6 = 路径结尾的 \bin\ 字符串的长度
set _PWD=%_PWD:~0,-5%

set PORTABLE_HOME=%_PWD%
set PYTHONHOME=%_PWD%\Portable Python 2.7.3.1\App
set SVN_HOME=%_PWD%\bin\svn-win32-1.6.15\bin
set GRAPHVIZ_HOME=%_PWD%\bin\Graphviz2.26.3\bin
set SQLITE_HOME=%_PWD%\bin\sqlite-shell-win32-x86-3071401

set PATH=%PATH%;%PYTHONHOME%;%SVN_HOME%

:: Trac 相关的程序独立于 Python 安装
set TRAC_INSTALL_PATH=%_PWD%\trac
set PYTHONPATH=%TRAC_INSTALL_PATH%\Lib\site-packages

set TRACENV=%_PWD%\tracenv

:: PlantUML 需要 GRAPHVIZ_DOT 环境变量
set GRAPHVIZ_DOT=%GRAPHVIZ_HOME%\dot.exe

set PROMPT=$G$G$G 

:: 构造一个简单的 timestamp, 供某些脚本使用(注意: 取决于操作系统设置, 不同运行环境下日期的格式可能不同)
set TIMESTAMP=%date% %time%
:: 替换某些 DOS 命令行特定的字符
set TIMESTAMP=%TIMESTAMP:\=-%
set TIMESTAMP=%TIMESTAMP:/=-%
set TIMESTAMP=%TIMESTAMP::=-%
echo [Current timestamp: %TIMESTAMP%]