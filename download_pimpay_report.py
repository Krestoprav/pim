# -*- coding: utf-8 -*-

import os
import time
import re
from twocaptcha import TwoCaptcha

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# --- ВАЖНО: ЗАМЕНИТЕ НА СВОЙ API КЛЮЧ ОТ 2CAPTCHA ---
API_KEY_2CAPTCHA = '824939cb4ba628af1d76f965e607a953'
# ---------------------------------------------------

# Получаем путь к директории, где находится скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))

# Настройка опций Chrome
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")

# Настройка папки для скачивания
download_dir = os.path.join(script_dir, "download")
os.makedirs(download_dir, exist_ok=True)

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

driver = uc.Chrome(options=options)

try:
    # Инициализация клиента 2captcha
    # Используем подход, аналогичный вашему предыдущему вопросу
    api_key = os.getenv('RUCAPTCHA_API_KEY', API_KEY_2CAPTCHA) # Попробуем сначала переменную окружения
    if api_key == API_KEY_2CAPTCHA:
        print("ВНИМАНИЕ: API-ключ задан напрямую в коде. Рассмотрите использование переменных окружения.")
    config = {
        'apiKey': api_key,
        'defaultTimeout': 180,
        'recaptchaTimeout': 600,
        'pollingInterval': 10
    }
    solver = TwoCaptcha(**config)

    # Переходим на страницу входа
    print("Открываю страницу входа...")
    driver.get("https://sso.pimpay.ru/site/login")

    # Максимизировать окно браузера
    driver.maximize_window()
    print("Окно браузера развернуто.")

    # Ждём загрузки страницы
    wait = WebDriverWait(driver, 10)

    # Вводим логин
    login_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
    login_field.send_keys("bochaevsr@yandex.ru")
    print("Логин введён.")

    # Вводим пароль
    password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']")))
    password_field.send_keys("B0ch@3v")
    print("Пароль введён.")

    # --- Решение reCAPTCHA v2 через 2captcha ---
    print("Поиск элемента reCAPTCHA...")
    # Найдём iframe, содержащий reCAPTCHA
    # Используем селектор из вашей предыдущей попытки
    recaptcha_frame = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='google.com/recaptcha/api2/anchor']")))
    print("Фрейм reCAPTCHA найден.")

    # Извлекаем sitekey из src iframe
    frame_src = recaptcha_frame.get_attribute('src')
    sitekey_match = re.search(r'[?&]k=([^&]+)', frame_src)
    if sitekey_match:
        sitekey = sitekey_match.group(1)
        print(f"Найден sitekey: {sitekey}")
    else:
        print("НЕ УДАЛОСЬ НАЙТИ sitekey в src iframe. Проверьте HTML страницы.")
        raise Exception("Sitekey не найден.")

    # Получаем URL текущей страницы
    page_url = driver.current_url
    print(f"URL страницы: {page_url}")

    # Отправляем задачу на решение CAPTCHA
    print("Отправляю задачу на решение CAPTCHA в 2captcha...")
    try:
        result = solver.recaptcha(sitekey=sitekey, url=page_url)
        g_response_token = result['code']
        print("CAPTCHA решена. Получен g-response token.")
    except Exception as e:
        print(f"Ошибка при решении CAPTCHA через 2captcha: {e}")
        raise

    # Вставляем полученный токен в скрытое поле и вызываем события
    # Найдём скрытое поле с id 'g-recaptcha-response'
    # Иногда оно может быть создано динамически, добавим небольшую задержку и ожидание
    time.sleep(1)
    driver.execute_script(f"document.getElementById('g-recaptcha-response').value = '{g_response_token}';")
    print("Токен вставлен в скрытое поле.")

    # Вызовем событие изменения, чтобы сайт узнал о новом значении
    driver.execute_script("document.getElementById('g-recaptcha-response').dispatchEvent(new Event('change'));")
    print("Событие 'change' вызвано для скрытого поля.")

    # --- Конец решения reCAPTCHA ---

    # Нажимаем кнопку "Войти"
    print("Поиск кнопки 'Войти'...")
    submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    submit_button.click()
    print("Кнопка 'Войти' нажата.")

    # Ждём загрузки главной страницы или перенаправления
    print("Жду загрузки главной страницы после входа...")
    time.sleep(5)

    # Переходим на страницу с датами (убраны лишние пробелы)
    print("Перехожу на страницу отчёта...")
    driver.get("https://cabinet2.pimpay.ru/report/balance/?dateStart=01.01.2026&dateEnd=31.12.2026")

    # Ждём появление ссылки "скачать в Excel" и кликаем по ней
    print("Жду появления ссылки для скачивания Excel...")
    excel_download_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.button--download[href*='xls']")))
    print("Ссылка для скачивания найдена.")
    excel_download_link.click()
    print("Клик по ссылке скачивания выполнен.")

    # Ждём завершения скачивания
    print("Жду завершения скачивания файла...")
    time.sleep(10) # Увеличьте, если файл большой

    # Проверка файла (по аналогии с предыдущим примером)
    files_in_dir = os.listdir(download_dir)
    xls_files = [f for f in files_in_dir if f.lower().endswith('.xls') or f.lower().endswith('.xlsx')]
    if xls_files:
        latest_file = max([os.path.join(download_dir, f) for f in xls_files], key=os.path.getctime)
        print(f"Файл успешно скачан: {latest_file}")
    else:
        print("Предупреждение: Файл .xls/.xlsx не найден в папке загрузки после ожидания.")

    print("Скрипт завершён успешно.")

except Exception as e:
    print(f"Произошла ошибка: {type(e).__name__}: {e}")

finally:
    # Аккуратно закрываем браузер
    print("Закрываю браузер...")
    try:
        driver.quit()
    except OSError as oe:
        # Игнорируем конкретную ошибку "Неверный дескриптор"
        if "Неверный дескриптор" in str(oe) or oe.errno == 6:
            print("Браузер, возможно, уже был закрыт. Игнорирую ошибку закрытия.")
        else:
            print(f"Другая ошибка OS при закрытии: {oe}")
    except Exception as e:
        print(f"Ошибка при закрытии браузера: {e}")
    print("Браузер закрыт.")
