import subprocess
import sys

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