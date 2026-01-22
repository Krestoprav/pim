# -*- coding: utf-8 -*-
import sys
import os

# Кодировка для Windows консоли
os.system('chcp 65001 > nul')
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

from db_setup import CONN_STRING


def main():
    print("=" * 60)
    print("ВЫГРУЗКА ТАБЛИЦЫ excel_data ИЗ CLOUD SQL В EXCEL")
    print("=" * 60)

    try:
        engine = create_engine(CONN_STRING)
    except Exception as e:
        print(f"[ERROR] Не удалось создать подключение к БД: {e}")
        return

    # Проверим, есть ли таблица
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT to_regclass('public.excel_data') IS NOT NULL AS exists_flag"
            ))
            exists = result.scalar()

        if not exists:
            print("[INFO] Таблица 'excel_data' пока не существует.")
            return
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке существования таблицы: {e}")
        return

    # Читаем всю таблицу
    try:
        df = pd.read_sql_query("SELECT * FROM excel_data", engine)
        # Сортируем по дате, если столбец 'Дата' присутствует
        if "Дата" in df.columns:
            try:
                df["Дата"] = pd.to_datetime(df["Дата"])
            except Exception:
                # если не удаётся привести к дате, сортируем как есть
                pass
            df = df.sort_values(by="Дата")
        print(f"[OK] Прочитано строк: {len(df)}")
    except Exception as e:
        print(f"[ERROR] Ошибка при чтении данных из 'excel_data': {e}")
        return

    # Сохраняем в Excel
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(script_dir, "exports")
        os.makedirs(out_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"excel_data_export_{timestamp}.xlsx"
        out_path = os.path.join(out_dir, filename)

        df.to_excel(out_path, index=False)
        print(f"[OK] Выгружено в файл: {out_path}")
    except Exception as e:
        print(f"[ERROR] Ошибка при сохранении Excel: {e}")
        return

    print("\n" + "=" * 60)
    print("Готово")
    print("=" * 60)


if __name__ == "__main__":
    main()


