import re
import sys

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