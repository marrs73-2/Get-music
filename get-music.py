#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
import re
from pathlib import Path


# ─────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────

def run_command(cmd, description=""):
    """Запускает внешнюю команду и проверяет ошибки."""
    print(f"\n▶ {description}...")
    print(f"  Команда: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  ✓ Успешно")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Ошибка: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"  ✗ Программа не найдена. Установите: {cmd[0]}")
        sys.exit(1)


def sanitize_filename(name):
    """Очищает строку от недопустимых символов для имён файлов."""
    # Заменяем недопустимые символы на пробелы
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Убираем лишние пробелы по краям
    name = name.strip()
    # Заменяем множественные пробелы на один
    name = re.sub(r'\s+', ' ', name)
    return name


def parse_metadata_overrides(note_str):
    """
    Парсит метаданные вида {key="value"} из строки заметки.
    Возвращает: (словарь_переопределений, оставшийся_комментарий)
    """
    if not note_str:
        return {}, ""
    
    # Ищем все вхождения {ключ="значение"}
    pattern = re.compile(r'\{(\w+)\s*=\s*"([^"]*)"\}')
    overrides = {}
    
    for match in pattern.finditer(note_str):
        key, value = match.groups()
        overrides[key.lower()] = value  # нормализуем ключи к нижнему регистру
        
    # Удаляем найденные конструкции из строки, чтобы получить чистый комментарий
    comment = pattern.sub('', note_str).strip()
    return overrides, comment


def parse_timestamps(filepath):
    """
    Парсит файл таймкодов формата:
        0:00 london song | flash warning
        3:15 ipod touch
    
    Возвращает список словарей:
        [{'start': '0:00', 'title': 'london song', 'overrides': {}, 'comment': 'flash warning'}, ...]
    """
    tracks = []
    pattern = re.compile(r'^((?:\d{0,2}:)?\d{1,2}:\d{2})\s*(?:[-—]\s*)?(.+?)(?:\s*\|\s*(.+))?$')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            match = pattern.match(line)
            if not match:
                print(f"  ⚠ Пропущена строка {line_num}: {line}")
                continue
            
            
            time_str = match.group(1)
            print(f"time_stamp = {time_str}")
            title = match.group(2).strip()
            raw_note = match.group(3).strip() if match.group(3) else ""

            #  Новая логика: разделяем заметку на переопределения и комментарий
            overrides, comment = parse_metadata_overrides(raw_note)
            
            tracks.append({
                'start': time_str,
                'title': title,
                'overrides': overrides,
                'comment': comment
            })
    
    if not tracks:
        print("  ✗ Не найдено ни одного валидного таймкода!")
        sys.exit(1)
    
    print(f"  Найдено треков: {len(tracks)}")
    return tracks


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


# ─────────────────────────────────────────────
# Основные шаги
# ─────────────────────────────────────────────

def download_album(url, output_dir):
    """Скачивает альбом через yt-dlp."""
    #output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
    output_path = os.path.join(output_dir, 'downloaded_song.mp3')
    
    cmd = [
        'yt-dlp',
        '-x',                          # Извлечь только аудио
        '--audio-format', 'mp3',       # Формат MP3
        '--audio-quality', '0',        # Максимальное качество
        '-o', output_path,         # Шаблон имени
        '--no-playlist',               # Не скачивать плейлист (если это один видео)
        '--print', 'after_move:filepath',  # Вывести путь к скачанному файлу,
        '--remote-components', 'ejs:github',
        url
    ]
    
    #output = run_command(cmd, "Скачивание альбома через yt-dlp")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("  ✗ Ошибка при скачивании через yt-dlp")
        sys.exit(1)
    except FileNotFoundError:
        print("  ✗ yt-dlp не установлен. Установите его через pip или apt.")
        sys.exit(1)
    
    downloaded_file = output_path  # Предполагаем, что файл будет сохранён именно по этому пути
    
    if not os.path.exists(downloaded_file):
        print(f"  ✗ Файл не найден после скачивания: {downloaded_file}")
        sys.exit(1)
    
    print(f"  Скачан файл: {downloaded_file}")
    return downloaded_file


def split_and_tag(input_file, tracks, output_dir, album_artist, album, genre, year):
    """Нарезает файл на треки и прописывает теги."""
    duration = get_audio_duration(input_file)
    
    for i, track in enumerate(tracks, 1):
        track_num = str(i).zfill(2)
        title = track['title']
        start_sec = time_to_seconds(track['start'])
        
        # Вычисляем время окончания
        if i < len(tracks):
            end_sec = time_to_seconds(tracks[i]['start'])
        else:
            # Последний трек — до конца файла
            end_sec = duration
        
        # Формируем имя файла
        safe_title = sanitize_filename(title)
        output_filename = f"{track_num} — {safe_title}.mp3"
        output_path = os.path.join(output_dir, output_filename)
    

	# ─── Собираем метаданные динамически ───
        meta = {
            'title': title,
            'album_artist': album_artist,      # Глобальный исполнитель
	        'artist': album_artist, 
            'album': album,
            'track': track_num,
            'tracknumber': track_num
        }
        if genre:
            meta['genre'] = genre
        if year:
            meta['date'] = year

        # Применяем точечные переопределения из таймкодов
        if track.get('overrides'):
            # Разрешаем переопределять только безопасные поля
            allowed_keys = {'artist', 'title', 'album', 'genre', 'comment'}
            for k, v in track['overrides'].items():
                if k in allowed_keys:
                    meta[k] = v
                elif k == 'performer':  # ffmpeg использует 'artist', но иногда пишут performer
                    meta['artist'] = v

        # Добавляем обычный комментарий, если он остался после {}
        if track.get('comment'):
            meta['comment'] = track['comment']

        # Преобразуем словарь в аргументы для ffmpeg: ['-metadata', 'key=val', ...]
        meta_args = []
        for k, v in meta.items():
            meta_args.extend(['-metadata', f'{k}={v}'])
        
        # Собираем итоговую команду
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-ss', seconds_to_ffmpeg_time(start_sec),
            '-to', seconds_to_ffmpeg_time(end_sec),
            '-c', 'copy', 
        ] + meta_args + [  # Вставляем метаданные в середину команды
            '-y', 
            output_path
        ]
        
        
        run_command(cmd, f"Нарезка трека {track_num}: {title}")
    
def download_and_tag_single(url, output_dir, performer, custom_title, date=None, genre=None, album=None, album_artist=None):
    """Скачивает один трек и сразу прописывает ему теги."""
    
    # 1. Скачиваем во временный файл, чтобы ffmpeg мог безопасно создать финальный
    #temp_template = os.path.join(output_dir, 'temp_single.%(ext)s')
    output_path = os.path.join(output_dir, 'downloaded_song_temporary.mp3')
    
    cmd = [
        'yt-dlp', '-x', '--audio-format', 'mp3', '--audio-quality', '0',
        '-o', output_path, '--no-playlist',
        '--print', 'after_move:filepath',         '--remote-components', 'ejs:github', url
    ]
    
    # Преобразуем список в строку для os.system
    print(f"\n▶ Скачивание сингла через yt-dlp...")
    # os.system выводит напрямую в консоль без буферизацииs

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("  ✗ Ошибка при скачивании через yt-dlp")
        sys.exit(1)
    except FileNotFoundError:
        print("  ✗ yt-dlp не установлен. Установите его через pip или apt.")
        sys.exit(1)
    
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
        'ffmpeg', '-i', temp_file, '-c', 'copy'
    ] + meta_args + ['-y', final_path]
    
    run_command(cmd_tag, f"Тегирование сингла: {title}")

    # 5. Удаляем временный файл
    if os.path.exists(temp_file) and temp_file != final_path:
        os.remove(temp_file)
        
    print(f"  💾 Сингл сохранен: {final_path}")

def cleanup(input_file):
    """Удаляет исходный скачанный файл."""
    if os.path.exists(input_file):
        os.remove(input_file)
        print(f"\n🗑 Удалён исходный файл: {input_file}")


# ─────────────────────────────────────────────
# Главная функция
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Скачивает альбом с YouTube, парсит таймкоды и нарезает на треки с тегами.'
    )
    parser.add_argument('-aa', '--album_artist', required=False, default=None, help='Имя исполнителя')
    parser.add_argument('-g', '--genre', required=False, default=None, help='Жанр альбома')
    parser.add_argument('-p', '--performer', required=False, default=None, help='Имя исполнителя для сингла')
    parser.add_argument('-a', '--album', required=False, default=None, help='Название альбома')
    parser.add_argument('-u', '--url', required=True, help='Ссылка на альбом (YouTube)')
    parser.add_argument('-t', '--timestamps', required=False, default="timestamps.txt", help='Путь к файлу с таймкодами')
    parser.add_argument('-k', '--keep-original', action='store_true', 
                        help='Не удалять исходный скачанный файл')
    parser.add_argument("-y", '--year', default=None, 
                    help='Год выпуска альбома (необязательно)')
    
    args = parser.parse_args()
    
    if ".txt" not in args.timestamps:
        print(f"Видео скачивается как сингл, название трека - {args.timestamps}")
        # Создаём выходную папку
        folder_name = f"{args.performer} - {args.timestamps}"
        output_dir = Path(folder_name)
        output_dir.mkdir(exist_ok=True)
        print(f"📁 Выходная папка: {output_dir}")

        #def download_and_tag_single(url, output_dir, performer,  custom_title, album=None, genre=None, album_artist=None):
        download_and_tag_single(args.url, str(output_dir), 
                                args.performer, args.timestamps, date=args.year, album=args.album, genre=args.genre, 
                                album_artist=args.album_artist)

    else:
        print(f"Видео скачивается как альбом")
        # Проверяем существование файла с таймкодами
        if not os.path.exists(args.timestamps):
            print(f" Файл с таймкодами не найден: {args.timestamps}")
            sys.exit(1)
        
        # Создаём выходную папку
        folder_name = f"{args.album_artist} - {args.album}"
        output_dir = Path(folder_name)
        output_dir.mkdir(exist_ok=True)
        print(f"📁 Выходная папка: {output_dir}")
        
        # Парсим таймкоды
        print("\n📋 Парсинг таймкодов...")
        tracks = parse_timestamps(args.timestamps)
        
        # Скачиваем альбом
        print("\n️  Скачивание...")
        downloaded_file = download_album(args.url, str(output_dir))
        
        # Нарезаем и тегируем
        print("\n✂️  Нарезка и тегирование...")
        split_and_tag(downloaded_file, tracks, str(output_dir), args.album_artist, args.album, args.genre, args.year)
        
        # Очистка
        if not args.keep_original:
            cleanup(downloaded_file)
        
        print(f"\n✅ Готово! {len(tracks)} треков сохранены в папку: {output_dir}")


if __name__ == '__main__':
    main()