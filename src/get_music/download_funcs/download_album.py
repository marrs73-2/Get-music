import sys
import os
from get_music.aux.small_functions import *
from get_music.aux.run_command import run_command

def download_album(url, output_dir):
    """Скачивает альбом через yt-dlp."""
    #output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
    output_path = os.path.join(output_dir, 'downloaded_song.mp3')
    
    cmd = [
        'yt-dlp',
        '-x',                          # Извлечь только аудио
        '--audio-format', 'mp3',       # Формат MP3
        '--audio-quality', '100K',        # Максимальное качество
        '-o', output_path,         # Шаблон имени
        '--no-playlist',               # Не скачивать плейлист (если это один видео)
        '--print', 'after_move:filepath',  # Вывести путь к скачанному файлу,
        '--remote-components', 'ejs:github',
        url
    ]
    
    run_command(cmd, "Скачивание альбома через yt-dlp")
    
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
            '-loglevel', 'error',
        ] + meta_args + [  # Вставляем метаданные в середину команды
            '-y', 
            output_path
        ]
        
        
        run_command(cmd, f"Нарезка трека {track_num}: {title}")