import subprocess
import sys
import os
from get_music.aux.run_command import run_command

def download_cover(url, output_dir):
    """Скачивает обложку альбома через yt-dlp."""
    output_path = os.path.join(output_dir, 'cover')
    
    cmd = [
        'yt-dlp',
        '--skip-download',              # Не скачивать видео
        '--write-thumbnail',            # Скачать обложку
        '--convert-thumbnails', 'jpg',  # Конвертировать в JPG
        '-o', output_path,              # Шаблон имени
        url
    ]
    
    try:
        run_command(cmd, f"Скачивание обложки через yt-dlp")
    except subprocess.CalledProcessError:
        print("  ✗ Ошибка при скачивании обложки через yt-dlp")
        sys.exit(1)
    except FileNotFoundError:
        print("  ✗ yt-dlp не установлен. Установите его через pip или apt.")
        sys.exit(1)
    
    if not os.path.exists(output_path+".jpg"):
        print(f"  ✗ Обложка не найдена после скачивания: {output_path}")
        sys.exit(1)
    
    print(f"  Скачана обложка: {output_path}")

    cmd2 = ['ffmpeg', '-y',
            '-i', f"{output_path}.jpg",
            '-vf', "crop='min(iw,ih)':'min(iw,ih)'",
            '-update', '1',
            '-loglevel', 'error',
            f"{output_path}.jpg"
    ]

    run_command(cmd2, f"Приведение обложки к квадратной форме через ffmpeg")
    print(f"Обложка приведена к квадратной форме: {output_path}.jpg")

    return output_path