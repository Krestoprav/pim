import sys
import os

# Устанавливаем кодировку UTF-8 для Windows консоли
os.system('chcp 65001 > nul')
sys.stdout.reconfigure(encoding='utf-8')

import glob
import pandas as pd
from sqlalchemy import create_engine, inspect

from db_setup import CONN_STRING  # используем общую строку подключения


# Название таблицы в Cloud SQL, куда будут загружены данные из Excel
# Вы можете поменять имя таблицы, если нужно
TARGET_TABLE = 'excel_data'


def main():
    print("=" * 60)
    print(f"Загрузка всех Excel-файлов из папки 'download' в таблицу '{TARGET_TABLE}' в Cloud SQL (PostgreSQL)")
    print("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(script_dir, "download")

    # 1. Ищем все Excel-файлы в download
    excel_files = sorted(
        f for f in glob.glob(os.path.join(download_dir, "*.xls*"))
        if not os.path.basename(f).startswith("~$")
    )
    if not excel_files:
        print(f"[INFO] В папке '{download_dir}' нет Excel-файлов (*.xls, *.xlsx).")
        return

    print("[INFO] Найдены файлы для загрузки:")
    for f in excel_files:
        print(f"  - {os.path.basename(f)}")

    # 2. Читаем и объединяем все файлы
    frames = []
    try:
        for path in excel_files:
            df_part = pd.read_excel(path)
            frames.append(df_part)
        df_new = pd.concat(frames, ignore_index=True)
        print(f"[OK] Файлы прочитаны и объединены")
        print(f"    Строк (новых):   {len(df_new)}")
        print(f"    Колонок:         {len(df_new.columns)}")
        print("    Колонки:", list(df_new.columns))
    except Exception as e:
        print(f"[ERROR] Не удалось прочитать один из файлов Excel: {e}")
        return

    # 3. Создаём подключение к базе
    try:
        engine = create_engine(CONN_STRING)
    except Exception as e:
        print(f"[ERROR] Не удалось создать подключение к БД: {e}")
        return

    # 4. Проверяем, существует ли таблица, и объединяем с уже существующими данными
    try:
        inspector = inspect(engine)
        table_exists = inspector.has_table(TARGET_TABLE)

        if table_exists:
            print(f"[INFO] Таблица '{TARGET_TABLE}' уже существует. Читаем текущие данные...")
            df_old = pd.read_sql_table(TARGET_TABLE, engine)
            print(f"    Строк (в базе до): {len(df_old)}")

            # Объединяем старые и новые данные
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        else:
            print(f"[INFO] Таблица '{TARGET_TABLE}' ещё не существует. Создаём её с нуля.")
            df_all = df_new

        # Удаляем дубли.
        # ЛОГИКА: считаем строку дублем, если совпадают ВСЕ 5 полей из Excel.
        # Если нужно другое условие (например, только по дате+сумме+компании),
        # можно поменять список колонок в subset.
        subset_cols = ['Дата', 'Операция', 'Сумма операции, р', 'Компания', 'Комментарий']
        missing_cols = [c for c in subset_cols if c not in df_all.columns]
        if missing_cols:
            print(f"[WARN] Не все ожидаемые колонки найдены в данных, удаление дублей по всем столбцам.")
            df_all = df_all.drop_duplicates()
        else:
            df_all = df_all.drop_duplicates(subset=subset_cols)

        print(f"    Строк (после объединения и удаления дублей): {len(df_all)}")

    except Exception as e:
        print(f"[ERROR] Ошибка при объединении данных: {e}")
        return

    # 5. Сохраняем итоговые данные в таблицу
    try:
        # Всегда пересоздаём таблицу, но уже с объединёнными и очищенными данными
        df_all.to_sql(TARGET_TABLE, engine, if_exists='replace', index=False)
        print(f"[OK] Данные сохранены в таблицу '{TARGET_TABLE}'")
    except Exception as e:
        print(f"[ERROR] Ошибка при сохранении данных в таблицу '{TARGET_TABLE}': {e}")
        return

    print("=" * 60)
    print("Загрузка и обновление с исключением дублей завершены")
    print("=" * 60)


if __name__ == "__main__":
    main()

