import argparse
import json
import logging
from datetime import date, datetime
from typing import Any, Dict

import pandas as pd

from src.reports import spending_by_category
from src.services import analyze_cashback_categories
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
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def services_page(df: pd.DataFrame, date_str: str) -> Dict[str, Any]:
    """
    Страница Сервисы. Вызывает бизнес-логику из services.py
    """
    logger.info("Генерация данных для страницы Сервисы")
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        cashback_analysis = analyze_cashback_categories(
            df.to_dict(orient="records"),
            year=date_obj.year,
            month=date_obj.month
        )
        return {
            "page": "services",
            "cashback_analysis": cashback_analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка в services_page: {str(e)}")
        return {"error": str(e)}


def reports_page(file_path: str, category: str, date_str: str) -> Dict[str, Any]:
    """
    Страница Отчеты. Вызывает бизнес-логику из reports.py
    """
    logger.info("Генерация данных для страницы Отчеты")
    try:
        report_df = spending_by_category(
            file_path, category=category, date=date_str, skip_save=True
        )
        return {
            "page": "reports",
            "report": report_df.to_dict(orient="records"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка в reports_page: {str(e)}")
        return {"error": str(e)}


def get_greeting(date_obj: datetime) -> str:
    hour = date_obj.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def generate_home_data(df: pd.DataFrame, date_str: str) -> Dict[str, Any]:
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = date_obj.replace(day=1)

        filtered_df = filter_transactions_by_date(df, start_date, date_obj)

        # Данные по картам
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

        # Топ-5 транзакций
        top_transactions = []
        if not filtered_df.empty and 'amount' in filtered_df.columns:
            top_trans = filtered_df.nlargest(5, 'amount')[['date', 'amount', 'category', 'description']]
            for _, row in top_trans.iterrows():
                transaction = row.to_dict()
                if isinstance(transaction.get('date'), (datetime, date)):
                    transaction['date'] = transaction['date'].isoformat()
                top_transactions.append(transaction)

        return {
            'greeting': get_greeting(date_obj),
            'cards': cards,
            'top_transactions': top_transactions,
            'currency_rates': get_currency_rates(),
            'stock_prices': get_stock_prices(),
            'analysis_date': date_str
        }
    except Exception as e:
        logger.error(f"Ошибка при генерации данных: {str(e)}")
        raise


def main_function() -> None:
    try:
        parser = argparse.ArgumentParser(description='Анализ банковских транзакций')
        parser.add_argument('file', help='Excel или CSV файл с транзакциями')
        parser.add_argument('--date',
                            default=datetime.now().strftime('%Y-%m-%d'),
                            help='Дата анализа в формате YYYY-MM-DD')
        args = parser.parse_args()

        logger.info(f"Старт анализа для даты {args.date}")

        df = load_transactions(args.file)

        result = generate_home_data(df, args.date)
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
    try:
        print("=== ДОМАШНЯЯ СТРАНИЦА ===")
        test_df = pd.DataFrame({
            'date': [datetime.now()],
            'amount': [-500, -1200, 1000],
            'card_last_digits': ['1234', '1234', '5678'],
            'category': ['Еда', 'Развлечения', 'test'],
            'description': ['покупка еды', 'кино', 'тест']
        })
        home_data = generate_home_data(test_df, datetime.now().strftime('%Y-%m-%d'))
        print(json.dumps(home_data, indent=2, ensure_ascii=False, default=datetime_encoder))

        print("\n=== СТРАНИЦА СЕРВИСЫ ===")
        services_data = services_page(test_df, datetime.now().strftime('%Y-%m-%d'))
        print(json.dumps(services_data, indent=2, ensure_ascii=False))

        print("\n=== СТРАНИЦА ОТЧЕТЫ ===")
        # передаём временный csv файл для теста
        test_file = "test_transactions.csv"
        test_df.to_csv(test_file, index=False)
        reports_data = reports_page(test_file, category="Еда", date_str=datetime.now().strftime('%Y-%m-%d'))
        print(json.dumps(reports_data, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Ошибка при запуске всех страниц: {str(e)}")
        print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    main_function()