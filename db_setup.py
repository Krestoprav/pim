# setup_database.py
import sys
import os

# Устанавливаем кодировку UTF-8 для Windows
os.system('chcp 65001 > nul')
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import create_engine, text

# Настройки подключения
DB_CONFIG = {
    'host': '34.32.31.226',
    'database': 'postgres',
    'user': 'pim',
    'password': 'pim',
    'port': 5432
}

CONN_STRING = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"


def create_tables():
    """Создание таблиц в Cloud SQL"""

    try:
        engine = create_engine(CONN_STRING)

        with engine.begin() as conn:
            print("=" * 60)
            print("СОЗДАНИЕ ТАБЛИЦ В CLOUD SQL")
            print("=" * 60)

            # 1. Таблица продаж
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sales (
                    id SERIAL PRIMARY KEY,
                    sale_date DATE NOT NULL,
                    product_id VARCHAR(50),
                    product_name VARCHAR(255),
                    category VARCHAR(100),
                    quantity INTEGER DEFAULT 0,
                    unit_price DECIMAL(10,2),
                    total_amount DECIMAL(10,2),
                    region VARCHAR(100),
                    manager VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Таблица 'sales' создана")

            # 2. Таблица клиентов
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY,
                    client_code VARCHAR(50) UNIQUE,
                    client_name VARCHAR(255),
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    city VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Таблица 'clients' создана")

            # 3. Таблица товаров
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    product_code VARCHAR(50) UNIQUE,
                    product_name VARCHAR(255),
                    category VARCHAR(100),
                    sale_price DECIMAL(10,2),
                    stock INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Таблица 'products' создана")

            # Создаем индексы
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_code ON clients(client_code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_code ON products(product_code)"))
            print("[OK] Индексы созданы")

            print("\n" + "=" * 60)
            print("ТАБЛИЦЫ УСПЕШНО СОЗДАНЫ!")
            print("=" * 60)

        return True

    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        return False


def check_tables():
    """Проверка созданных таблиц"""

    try:
        engine = create_engine(CONN_STRING)

        with engine.connect() as conn:
            print("\n" + "=" * 60)
            print("ПРОВЕРКА ТАБЛИЦ")
            print("=" * 60)

            # Получаем список таблиц
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))

            tables = [row[0] for row in result.fetchall()]

            if tables:
                print("Найдены таблицы:")
                for table in tables:
                    # Получаем количество записей
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    print(f"  - {table}: {count} записей")
            else:
                print("Таблицы не найдены")

        return True

    except Exception as e:
        print(f"[ERROR] Ошибка проверки: {e}")
        return False


def add_test_data():
    """Добавление тестовых данных"""

    try:
        import pandas as pd
        from datetime import datetime, timedelta

        engine = create_engine(CONN_STRING)

        print("\n" + "=" * 60)
        print("ДОБАВЛЕНИЕ ТЕСТОВЫХ ДАННЫХ")
        print("=" * 60)

        # 1. Добавляем товары
        products = [
            {'product_code': 'P001', 'product_name': 'Ноутбук', 'category': 'Электроника', 'sale_price': 45000,
             'stock': 10},
            {'product_code': 'P002', 'product_name': 'Мышь', 'category': 'Аксессуары', 'sale_price': 1200, 'stock': 50},
            {'product_code': 'P003', 'product_name': 'Монитор', 'category': 'Электроника', 'sale_price': 18000,
             'stock': 8},
        ]

        with engine.begin() as conn:
            for product in products:
                conn.execute(text("""
                    INSERT INTO products (product_code, product_name, category, sale_price, stock)
                    VALUES (:code, :name, :category, :price, :stock)
                """), {
                    'code': product['product_code'],
                    'name': product['product_name'],
                    'category': product['category'],
                    'price': product['sale_price'],
                    'stock': product['stock']
                })
        print("[OK] Товары добавлены")

        # 2. Добавляем клиентов
        clients = [
            {'client_code': 'C001', 'client_name': 'Компания А', 'city': 'Москва'},
            {'client_code': 'C002', 'client_name': 'Компания Б', 'city': 'СПб'},
            {'client_code': 'C003', 'client_name': 'Компания В', 'city': 'Екатеринбург'},
        ]

        with engine.begin() as conn:
            for client in clients:
                conn.execute(text("""
                    INSERT INTO clients (client_code, client_name, city)
                    VALUES (:code, :name, :city)
                """), client)
        print("[OK] Клиенты добавлены")

        # 3. Добавляем продажи через pandas
        sales_data = []
        base_date = datetime.now().date()

        for i in range(20):
            product = products[i % len(products)]
            sales_data.append({
                'sale_date': base_date - timedelta(days=i),
                'product_id': product['product_code'],
                'product_name': product['product_name'],
                'category': product['category'],
                'quantity': 1 + (i % 3),
                'unit_price': product['sale_price'],
                'total_amount': (1 + (i % 3)) * product['sale_price'],
                'region': ['Москва', 'СПб', 'Новосибирск'][i % 3],
                'manager': ['Иванов', 'Петров', 'Сидоров'][i % 3]
            })

        df_sales = pd.DataFrame(sales_data)
        df_sales.to_sql('sales', engine, if_exists='append', index=False)
        print(f"[OK] {len(df_sales)} продаж добавлены")

        return True

    except Exception as e:
        print(f"[ERROR] Ошибка добавления данных: {e}")
        return False


def main():
    """Главная функция"""

    print("НАСТРОЙКА БАЗЫ ДАННЫХ CLOUD SQL")
    print("=" * 60)

    # 1. Создаем таблицы
    if not create_tables():
        print("\nНе удалось создать таблицы. Выход.")
        return

    # 2. Проверяем таблицы
    check_tables()

    # 3. Спрашиваем про тестовые данные
    print("\n" + "=" * 60)
    response = input("Добавить тестовые данные? (y/n): ")

    if response.lower() == 'y':
        if add_test_data():
            print("\n" + "=" * 60)
            print("ТЕСТОВЫЕ ДАННЫЕ ДОБАВЛЕНЫ!")
            print("=" * 60)

    # 4. Финальная проверка
    print("\n" + "=" * 60)
    print("БАЗА ДАННЫХ ГОТОВА!")
    print("=" * 60)
    print(f"Адрес: {DB_CONFIG['host']}")
    print(f"База: {DB_CONFIG['database']}")
    print(f"Пользователь: {DB_CONFIG['user']}")

    # Показываем структуру таблиц
    print("\nСТРУКТУРА ТАБЛИЦ:")
    print("-" * 40)

    engine = create_engine(CONN_STRING)
    with engine.connect() as conn:
        tables = ['sales', 'clients', 'products']
        for table in tables:
            result = conn.execute(text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """))

            print(f"\n{table}:")
            for row in result.fetchall():
                print(f"  {row[0]:20} {row[1]}")


if __name__ == "__main__":
    main()

