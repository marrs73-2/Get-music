import sys
import os
from get_music.aux.small_functions import *
from get_music.aux.run_command import run_command
from pathlib import Path


def download_and_tag_single(url, output_dir, performer, custom_title, date=None, genre=None, album=None, album_artist=None):
    """Скачивает один трек и сразу прописывает ему теги."""
    
    # 1. Скачиваем во временный файл, чтобы ffmpeg мог безопасно создать финальный
    #temp_template = os.path.join(output_dir, 'temp_single.%(ext)s')
    output_path = os.path.join(output_dir, 'downloaded_song_temporary.mp3')
    
    cmd = [
        'yt-dlp', '-x', '--audio-format', 'mp3', '--audio-quality', '100K',
        '-o', output_path, '--no-playlist',
        '--print', 'after_move:filepath',         '--remote-components', 'ejs:github', url
    ]
    
    # Преобразуем список в строку для os.system
    print(f"\n▶ Скачивание сингла через yt-dlp...")
    # os.system выводит напрямую в консоль без буферизацииs

    run_command(cmd, f"Скачивание сингла через yt-dlp")

    
    temp_file = output_path
    
    if not os.path.exists(temp_file):
        print(f"  ✗ Файл не найден после скачивания: {temp_file}")
        sys.exit(1)

    # 2. Определяем название и финальный путь
    # Если пользователь не задал --title, берем название из скачанного файла
    if custom_title:
        title = custom_title
    else:
        title = Path(temp_file).stem  # Убираем расширение .mp3
        
    safe_title = sanitize_filename(title)
    final_filename = f"{safe_title}.mp3"
    final_path = os.path.join(output_dir, final_filename)

    # 3. Собираем метаданные
    meta = {
        'title': title,
        'artist': performer,
    }
    if album_artist: meta['album_artist'] = album_artist
    if album: meta['album'] = album
    if genre: meta['genre'] = genre
    if date: meta['date'] = date

    meta_args = []
    for k, v in meta.items():
        meta_args.extend(['-metadata', f'{k}={v}'])

    # 4. Копируем из временного файла в финальный с тегами
    cmd_tag = [
        'ffmpeg', '-i', temp_file, '-c', 'copy', '-loglevel', 'error'
    ] + meta_args + ['-y', final_path]
    
    run_command(cmd_tag, f"Тегирование сингла: {title}")

    # 5. Удаляем временный файл
    if os.path.exists(temp_file) and temp_file != final_path:
        os.remove(temp_file)
        
    print(f"  💾 Сингл сохранен: {final_path}")
