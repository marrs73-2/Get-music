import subprocess
import sys
import os
import re


def sanitize_filename(name):
    """Очищает строку от недопустимых символов для имён файлов."""
    # Заменяем недопустимые символы на пробелы
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Убираем лишние пробелы по краям
    name = name.strip()
    # Заменяем множественные пробелы на один
    name = re.sub(r'\s+', ' ', name)
    return name

def get_audio_duration(filepath):
    """Получает длительность аудиофайла в секундах через ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"  ✗ Не удалось получить длительность файла: {e}")
        sys.exit(1)


def time_to_seconds(time_str):
    """Конвертирует 'М:СС' или 'ММ:СС' в секунды."""
    parts = time_str.split(':')
    if len(parts) == 2:
        minutes, seconds = parts
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    else:
        raise ValueError(f"Неверный формат времени: {time_str}")
    
    return int(minutes) * 60 + int(seconds)


def seconds_to_ffmpeg_time(seconds):
    """Конвертирует секунды в формат 'ЧЧ:ММ:СС.00' для ffmpeg."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"

def cleanup(input_file):
    """Удаляет исходный скачанный файл."""
    if os.path.exists(input_file):
        os.remove(input_file)
        print(f"\n🗑 Удалён исходный файл: {input_file}")