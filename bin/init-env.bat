set _PWD=%~dp0%
:: -6 = ·����β�� \bin\ �ַ����ĳ���
set _PWD=%_PWD:~0,-5%

set PORTABLE_HOME=%_PWD%
set PYTHONHOME=%_PWD%\Portable Python 2.7.3.1\App
set SVN_HOME=%_PWD%\bin\svn-win32-1.6.15\bin
set GRAPHVIZ_HOME=%_PWD%\bin\Graphviz2.26.3\bin
set SQLITE_HOME=%_PWD%\bin\sqlite-shell-win32-x86-3071401

set PATH=%PATH%;%PYTHONHOME%;%SVN_HOME%

:: Trac ��صĳ�������� Python ��װ
set TRAC_INSTALL_PATH=%_PWD%\trac
set PYTHONPATH=%TRAC_INSTALL_PATH%\Lib\site-packages

set TRACENV=%_PWD%\tracenv

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