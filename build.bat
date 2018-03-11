@echo off

where python
if errorlevel 1 goto nopython

:found_python
setlocal
for /f %%i in ('where python') do set PYPTH=%%~dpi
echo Python found at %PYPTH%

:: cx_Freeze requires the pywin32 dlls in the PATH. Unfortunately, they aren't always there so let's just add the path to them
set PYWIN32DLL_PATH=%PYPTH%\Lib\site-packages\pywin32_system32
set PATH=%PATH%;%PYWIN32DLL_PATH%

python setup.py build

exit /B 0

:nopython
    echo "No python found. Please make sure python is in the PATH"
    exit /B 1