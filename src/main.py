import argparse
import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Union

import pandas as pd

from src.utils import (
    calculate_cashback,
    filter_transactions_by_date,
    load_transactions,
    mask_card_number,
    setup_logging,
)
from src.views import get_currency_rates, get_stock_prices

setup_logging()
logger = logging.getLogger(__name__)


def datetime_encoder(obj: Any) -> Any:
    """
    Функция для сериализации datetime и date объектов в JSON.
    Решает проблему с ошибкой сериализации дат.

    Args:
        obj: Объект для сериализации

    Returns:
        Сериализуемый объект или вызывает исключение
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def services_page() -> Dict[str, Any]:
    """
    Функция для страницы Сервисы.

    Returns:
        Словарь с данными для страницы Сервисы
    """
    logger.info("Генерация данных для страницы Сервисы")
    try:
        # Здесь будет логика для страницы Сервисы
        return {
            "page": "services",
            "message": "Страница сервисов в разработке",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка в services_page: {str(e)}")
        return {"error": str(e)}


def reports_page() -> Dict[str, Any]:
    """
    Функция для страницы Отчеты.

    Returns:
        Словарь с данными для страницы Отчеты
    """
    logger.info("Генерация данных для страницы Отчеты")
    try:
        # Здесь будет логика для страницы Отчеты
        return {
            "page": "reports",
            "message": "Страница отчетов в разработке",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка в reports_page: {str(e)}")
        return {"error": str(e)}


def get_greeting(date_obj: datetime) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.

    Args:
        date_obj: Дата и время для определения приветствия

    Returns:
        Строка с приветствием
    """
    hour = date_obj.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def generate_home_data(df: pd.DataFrame, date_str: str) -> Dict[str, Any]:
    """
    Генерирует основные данные для домашней страницы приложения.

    Args:
        df: DataFrame с транзакциями
        date_str: Дата анализа в формате строки 'YYYY-MM-DD'

    Returns:
        Словарь с данными для отображения: карты, транзакции, курсы валют и акций
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        start_date = date_obj.replace(day=1)

        filtered_df = filter_transactions_by_date(df, start_date, date_obj)

        # Генерация данных по картам
        cards = []
        if 'card_last_digits' in filtered_df.columns:
            for card in filtered_df['card_last_digits'].unique():
                if pd.isna(card):
                    continue
                card_df = filtered_df[filtered_df['card_last_digits'] == card]
                total_spent = card_df[card_df['amount'] < 0]['amount'].sum() * -1
                cards.append({
                    'last_digits': mask_card_number(str(card)),
                    'total_spent': round(total_spent, 2),
                    'cashback': round(calculate_cashback(total_spent), 2)
                })

        # Топ-5 транзакций (преобразуем даты в строки)
        top_transactions = []
        if not filtered_df.empty and 'amount' in filtered_df.columns:
            top_trans = filtered_df.nlargest(5, 'amount')[['date', 'amount', 'category', 'description']]
            for _, row in top_trans.iterrows():
                transaction = row.to_dict()
                # Преобразуем datetime в строку для JSON
                if isinstance(transaction.get('date'), (datetime, date)):
                    transaction['date'] = transaction['date'].isoformat()
                top_transactions.append(transaction)

        # Получаем курсы валют и акций
        currency_rates = get_currency_rates()
        stock_prices = get_stock_prices()

        return {
            'greeting': get_greeting(date_obj),
            'cards': cards,
            'top_transactions': top_transactions,
            'currency_rates': currency_rates,
            'stock_prices': stock_prices,
            'analysis_date': date_str
        }
    except Exception as e:
        logger.error(f"Ошибка при генерации данных: {str(e)}")
        raise


def main_function() -> None:
    """
    Основная функция приложения - точка входа.
    Обрабатывает аргументы командной строки, загружает данные и генерирует отчет.

    Returns:
        None
    """
    try:
        parser = argparse.ArgumentParser(description='Анализ банковских транзакций')
        parser.add_argument('file', help='Excel или CSV файл с транзакциями')
        parser.add_argument('--date',
                            default=datetime.now().strftime('%Y-%m-%d'),
                            help='Дата анализа в формате YYYY-MM-DD')
        args = parser.parse_args()

        logger.info(f"Старт анализа для даты {args.date}")

        # Загрузка транзакций с обработкой ошибок
        df = load_transactions(args.file)

        # Генерация данных для домашней страницы
        result = generate_home_data(df, args.date)

        # Вывод результатов с правильной сериализацией дат
        print(json.dumps(result, indent=2, ensure_ascii=False, default=datetime_encoder))
        logger.info("Анализ успешно завершен")

    except FileNotFoundError:
        logger.error(f"Файл не найден: {args.file}")
        print(f"Ошибка: Файл {args.file} не найден")
    except Exception as e:
        logger.exception("Ошибка в работе приложения")
        print(f"Ошибка: {str(e)}")
        raise


def run_all_pages() -> None:
    """
    Запускает все страницы приложения и выводит результаты.
    """
    try:
        # Запуск основной функции
        print("=== ДОМАШНЯЯ СТРАНИЦА ===")
        # Для демонстрации создаем тестовый DataFrame
        test_df = pd.DataFrame({
            'date': [datetime.now()],
            'amount': [1000],
            'card_last_digits': ['1234'],
            'category': ['test'],
            'description': ['test transaction']
        })
        home_data = generate_home_data(test_df, datetime.now().strftime('%Y-%m-%d'))
        print(json.dumps(home_data, indent=2, ensure_ascii=False, default=datetime_encoder))

        print("\n=== СТРАНИЦА СЕРВИСЫ ===")
        services_data = services_page()
        print(json.dumps(services_data, indent=2, ensure_ascii=False))

        print("\n=== СТРАНИЦА ОТЧЕТЫ ===")
        reports_data = reports_page()
        print(json.dumps(reports_data, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Ошибка при запуске всех страниц: {str(e)}")
        print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    # Вызов основной функции
    main_function()