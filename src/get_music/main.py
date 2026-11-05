import argparse
import sys
import os
from pathlib import Path

from get_music.aux.parse_timestamps import parse_timestamps
from get_music.aux.small_functions import cleanup
from get_music.download_funcs.download_cover import download_cover
from get_music.download_funcs.download_album import download_album, split_and_tag
from get_music.download_funcs.download_single import download_and_tag_single


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
    parser.add_argument("-c", '--cover', required=False, action='store_true', 
                    help='Скачать обложку альбома')
    
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

        # Скачиваем обложку
        print("\n️  Скачивание обложки...")
        download_cover(args.url, str(output_dir))

        # Скачиваем альбом
        print("\n️  Скачивание альбома...")
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