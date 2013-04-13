set _PWD=%~dp0%
:: -5 = ·����β�� \bin\ �ַ����ĳ���
set _PWD=%_PWD:~0,-5%

:: Avoid iconv "unreadable code" console output
set LANG=en_US

set PORTABLE_HOME=%_PWD%
set PYTHONHOME=%_PWD%\PortablePython\App

set SVN_HOME=%_PWD%\bin\svn-win32-1.6.15\bin
set GIT_HOME=%_PWD%\bin\Git\bin

set GRAPHVIZ_HOME=%_PWD%\bin\graphviz\bin
set SQLITE_HOME=%_PWD%\bin\sqlite-shell-win32-x86-3071401

set PATH=%PATH%;%PYTHONHOME%;%SVN_HOME%;%GIT_HOME%

:: Trac ��صĳ�������� Python ��װ
set TRAC_INSTALL_PATH=%_PWD%\trac
set PYTHONPATH=%TRAC_INSTALL_PATH%\Lib\site-packages

IF NOT DEFINED SITE_BASE (
    set SITE_BASE=%_PWD%
)
set TRACENV=%SITE_BASE%\tracenv

:: PlantUML ��Ҫ GRAPHVIZ_DOT ��������
set GRAPHVIZ_DOT=%GRAPHVIZ_HOME%\dot.exe

set PROMPT=$G$G$G 

:: ����һ���򵥵� timestamp, ��ĳЩ�ű�ʹ��(ע��: ȡ���ڲ���ϵͳ����, ��ͬ���л��������ڵĸ�ʽ���ܲ�ͬ)
set TIMESTAMP=%date% %time%
:: �滻ĳЩ DOS �������ض����ַ�
set TIMESTAMP=%TIMESTAMP:\=-%
set TIMESTAMP=%TIMESTAMP:/=-%
set TIMESTAMP=%TIMESTAMP::=-%
echo [Current timestamp: %TIMESTAMP%]