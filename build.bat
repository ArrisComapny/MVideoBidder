@echo off
setlocal ENABLEDELAYEDEXPANSION

call .venv\Scripts\activate.bat

if not defined VIRTUAL_ENV (
    echo Ошибка: виртуальное окружение не активировано.
    exit /b 1
)

echo Сборка основного приложения...
python -m PyInstaller --noconfirm --clean my.spec
if errorlevel 1 (
    echo Сборка my.spec завершилась с ошибкой.
    goto :end
)

echo Сборка updater...
python -m PyInstaller --noconfirm --clean updater.spec
if errorlevel 1 (
    echo Сборка updater.spec завершилась с ошибкой.
    goto :end
)

set "APPDIR=dist\MVideoBidder"

:found_app
echo Найдена папка приложения: "%APPDIR%"

set "INTERNAL=%APPDIR%\_internal"
set "SRC=%INTERNAL%\browser"
set "DST=%APPDIR%\browser"

if not exist "%SRC%" (
    echo Перенос browser не требуется.
    goto :success
)

if exist "%DST%" (
    echo Папка "%DST%" уже существует, пропускаю перенос.
    goto :success
)

echo Переношу "%SRC%" -> "%DST%"
xcopy "%SRC%" "%DST%\" /E /I /Y
if errorlevel 1 (
    echo Ошибка при копировании папки browser.
    goto :end
)

rmdir /S /Q "%SRC%"

:success
echo Готово.

:end
pause
endlocal
