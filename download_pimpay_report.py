# -*- coding: utf-8 -*-

import os
import time

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Получаем путь к директории, где находится скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))

# Настройка опций Chrome
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")

# Настройка папки для скачивания
download_dir = os.path.join(script_dir, "download")

prefs = {
    "download.default_directory": download_dir,  # Папка для скачивания — та же, где скрипт
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

driver = uc.Chrome(options=options)

try:
    # Переходим на страницу входа
    driver.get("https://sso.pimpay.ru/site/login")

    # Максимизировать окно браузера
    driver.maximize_window()

    # Ждём загрузки страницы
    wait = WebDriverWait(driver, 10)

    # Вводим логин
    login_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
    login_field.send_keys("bochaevsr@yandex.ru")

    # Вводим пароль
    password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
    password_field.send_keys("B0ch@3v")

    # Переключаемся во фрейм, если капча в iframe
    try:
        iframe = wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[src*='google.com/recaptcha']")))
        print("Переключились во фрейм капчи")
    except:
        print("Капча не в iframe или ID изменился")

    # Ждём, пока чекбокс станет кликабельным
    recaptcha_checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.recaptcha-checkbox")))
    recaptcha_checkbox.click()

    # Переключаемся обратно в основной контекст
    driver.switch_to.default_content()

    # Пауза для ручного решения капчи
    print("Пожалуйста, решите капчу вручную (если она появилась)...")
    input("Нажмите Enter, когда капча будет решена...")

    # Нажимаем кнопку "Войти"
    submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    submit_button.click()

    # Ждём загрузки главной страницы
    time.sleep(5)

    # Переходим на страницу с датами
    driver.get("https://cabinet2.pimpay.ru/report/balance/?dateStart=01.01.2026&dateEnd=31.12.2026")

    # Ждём появление ссылки "скачать в Excel" и кликаем по ней
    excel_download_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.button--download[href*='xls']")))
    excel_download_link.click()

    # Ждём завершения скачивания
    time.sleep(60)

except Exception as e:
    print(f"Произошла ошибка: {e}")

finally:
    # Аккуратно закрываем браузер, игнорируя ошибки при повторном закрытии
    try:
        driver.quit()
    except Exception:
        pass
