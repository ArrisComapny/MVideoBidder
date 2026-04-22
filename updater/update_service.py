from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

from .updater_client import get_latest_release, is_update_available


logger = logging.getLogger("mvideo_bidder")


def download_file(
    url: str,
    path: Path,
    progress_callback=None,
    log_callback=None,
    retries: int = 3,
) -> None:
    last_error = None

    for attempt in range(1, retries + 1):
        downloaded = 0

        try:
            logger.info(f"Начало скачивания: url={url}")
            logger.info(f"Файл назначения: {path}")
            logger.info(f"Попытка скачивания {attempt}/{retries}")

            if log_callback:
                log_callback(f"Начало скачивания: {path.name}")
                log_callback(f"Попытка {attempt}/{retries}")

            with requests.get(url, stream=True, timeout=120, allow_redirects=True) as response:
                logger.info(f"Ответ сервера: status_code={response.status_code}")
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                content_type = response.headers.get("content-type", "")
                logger.info(f"Размер файла: {total_size} байт, content-type={content_type}")

                if log_callback:
                    log_callback(f"Ответ сервера: {response.status_code}")
                    log_callback(f"Размер файла: {total_size} байт")

                with open(path, "wb") as f:
                    last_logged_percent = -1

                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if not chunk:
                            continue

                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            logger.info(
                                f"Скачивание {path.name}: {downloaded}/{total_size} байт ({percent}%)"
                            )

                            if progress_callback:
                                progress_callback(percent)

                            if log_callback and percent != last_logged_percent:
                                log_callback(
                                    f"{path.name}: {downloaded}/{total_size} байт ({percent}%)"
                                )
                                last_logged_percent = percent
                        else:
                            logger.info(
                                f"Скачивание {path.name}: получено {downloaded} байт"
                            )
                            if log_callback:
                                log_callback(f"{path.name}: получено {downloaded} байт")

            final_size = path.stat().st_size if path.exists() else 0
            logger.info(f"Скачивание завершено: {path}, размер на диске={final_size} байт")

            if log_callback:
                log_callback(f"Скачивание завершено: {path.name}")
                log_callback(f"Размер на диске: {final_size} байт")

            return

        except Exception as e:
            last_error = e
            logger.exception(
                f"Ошибка скачивания файла {path.name} на попытке {attempt}/{retries}. "
                f"Успели скачать {downloaded} байт. Ошибка: {e}"
            )

            if log_callback:
                log_callback(
                    f"Ошибка скачивания {path.name} на попытке {attempt}/{retries}: {e}"
                )

            if path.exists():
                try:
                    bad_size = path.stat().st_size
                    logger.info(f"Удаляю недокачанный файл {path}, размер={bad_size} байт")

                    if log_callback:
                        log_callback(f"Удаляю недокачанный файл {path.name}, размер={bad_size} байт")

                    path.unlink()
                except Exception as delete_error:
                    logger.exception(f"Не удалось удалить битый файл {path}: {delete_error}")

                    if log_callback:
                        log_callback(f"Не удалось удалить битый файл {path.name}: {delete_error}")

            if attempt < retries:
                logger.info("Пауза 2 сек перед повторной попыткой")
                if log_callback:
                    log_callback("Пауза 2 сек перед повторной попыткой")
                time.sleep(2)

    raise last_error


def check_update() -> tuple[bool, str, object | None]:
    info = get_latest_release()
    if info is None:
        return False, "Не удалось получить данные релиза", None

    if not is_update_available(info.version):
        return False, "Обновление не требуется", None

    return True, f"Найдена новая версия {info.version}", info


def run_update(info, progress_callback=None, log_callback=None, status_callback=None) -> None:
    app_dir = Path(sys.executable).resolve().parent
    temp_dir = Path(tempfile.gettempdir()) / "mvideo_bidder_update"
    temp_dir.mkdir(parents=True, exist_ok=True)

    update_zip = temp_dir / "MVideoBidder_update.zip"
    updater_exe = temp_dir / "updater.exe"

    logger.info(f"Каталог приложения: {app_dir}")
    logger.info(f"Временная папка обновления: {temp_dir}")
    logger.info(f"URL архива обновления: {info.update_url}")
    logger.info(f"URL updater.exe: {info.updater_url}")

    if log_callback:
        log_callback(f"Каталог приложения: {app_dir}")
        log_callback(f"Временная папка обновления: {temp_dir}")
        log_callback(f"URL архива обновления: {info.update_url}")
        log_callback(f"URL updater.exe: {info.updater_url}")

    if status_callback:
        status_callback("Скачивание архива обновления...")

    def zip_progress(value: int):
        if progress_callback:
            progress_callback(int(value * 0.8))

    def updater_progress(value: int):
        if progress_callback:
            progress_callback(80 + int(value * 0.2))

    logger.info("Начинаю скачивание архива обновления")
    if log_callback:
        log_callback("Начинаю скачивание архива обновления")

    download_file(
        info.update_url,
        update_zip,
        progress_callback=zip_progress,
        log_callback=log_callback,
    )

    if status_callback:
        status_callback("Скачивание updater.exe...")

    logger.info("Начинаю скачивание updater.exe")
    if log_callback:
        log_callback("Начинаю скачивание updater.exe")

    download_file(
        info.updater_url,
        updater_exe,
        progress_callback=updater_progress,
        log_callback=log_callback,
    )

    if not update_zip.exists():
        raise FileNotFoundError(f"Архив обновления не найден после скачивания: {update_zip}")

    if not updater_exe.exists():
        raise FileNotFoundError(f"updater.exe не найден после скачивания: {updater_exe}")

    logger.info(f"Архив обновления скачан: {update_zip}, размер={update_zip.stat().st_size} байт")
    logger.info(f"updater.exe скачан: {updater_exe}, размер={updater_exe.stat().st_size} байт")

    if log_callback:
        log_callback(
            f"Архив обновления скачан: {update_zip.name}, размер={update_zip.stat().st_size} байт"
        )
        log_callback(
            f"updater.exe скачан: {updater_exe.name}, размер={updater_exe.stat().st_size} байт"
        )

    if status_callback:
        status_callback("Запуск установщика обновления...")

    if progress_callback:
        progress_callback(100)

    logger.info("Запускаю updater.exe")
    if log_callback:
        log_callback("Запускаю updater.exe")

    subprocess.Popen([
        str(updater_exe),
        "--zip", str(update_zip),
        "--app-dir", str(app_dir),
        "--exe-name", Path(sys.executable).name,
        "--pid", str(os.getpid()),
    ])