@echo off
setlocal
set JAVA_PATH=
set JAVA_EXE=java.exe
set JAVAC_EXE=javac.exe
set REQUIRED_JAVA_EXE_NAME=%JAVA_EXE%

:: FIX ME if JAVA_HOME is not set in the environment variable
set LOCAL_JAVA_HOME=C:\Program Files\OpenJDK\jdk-24.0.2
::set LOCAL_JAVA_HOME=c:\Program Files\Java\jdk-14.0.2

::
:: Check if java executable is in PATH
echo Checking if %REQUIRED_JAVA_EXE_NAME% is in PATH...
%REQUIRED_JAVA_EXE_NAME% -version
@if %ERRORLEVEL% == 0 (
    echo %REQUIRED_JAVA_EXE_NAME% found in PATH
    echo:
    goto main_run
)
::
:: Check JAVA_HOME environment variable
if not "%JAVA_HOME%" == "" (
    echo JAVA_HOME is "%JAVA_HOME%"
    echo:
    goto main_skip_java_home
)
echo WARNING: %REQUIRED_JAVA_EXE_NAME% not found in PATH or JAVA_HOME...
echo local variable JAVA_HOME set to "%LOCAL_JAVA_HOME%"

:main_skip_java_home
set JAVA_PATH=%LOCAL_JAVA_HOME%\bin\

::
:: Main
:main_run
set JAVA=%JAVA_PATH%%JAVA_EXE%
set JAVAC=%JAVA_PATH%%JAVAC_EXE%
set CLASS_DIR="classes"
set SRC_DIR="src"
:: Check again required java executable
"%JAVA%" -version
@if not %ERRORLEVEL% == 0 (
    echo ERROR: %REQUIRED_JAVA_EXE_NAME% not found...
    echo:
    echo You need to correct variable LOCAL_JAVA_HOME.
    echo:
    goto main_exit
)

echo Using %JAVA% to run...
set LIB_PCANBASIC_JAR=".\PCAN-Basic_java.jar"
if not exist "%LIB_PCANBASIC_JAR%" (
    echo ERROR: %LIB_PCANBASIC_JAR% not found
    echo:
    echo You need to copy library PCAN-Basic_java.jar in %LIB_PCANBASIC_JAR%.
    echo:
    goto main_exit
)

"%JAVA%" --class-path "%CLASS_DIR%;%LIB_PCANBASIC_JAR%;" peak.can.Application
@echo off

:main_exit
endlocal
