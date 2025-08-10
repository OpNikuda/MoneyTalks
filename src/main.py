import argparse
import json
from datetime import datetime, timedelta
import logging
import pandas as pd
from src.utils import (
    load_transactions,
    filter_transactions_by_date,
    calculate_cashback,
    mask_card_number,
    setup_logging
)

setup_logging()
logger = logging.getLogger(__name__)


def main_function():
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

        print(json.dumps(result, indent=2, ensure_ascii=False))
        logger.info("Анализ успешно завершен")

    except Exception as e:
        logger.exception("Ошибка в работе приложения")
        raise


def get_greeting(date: datetime) -> str:
    hour = date.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def generate_home_data(df: pd.DataFrame, date_str: str) -> dict:
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        start_date = date.replace(day=1)

        filtered_df = filter_transactions_by_date(df, start_date, date)

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

        # Топ-5 транзакций
        top_trans = pd.DataFrame()
        if not filtered_df.empty and 'amount' in filtered_df.columns:
            top_trans = filtered_df.nlargest(5, 'amount')[['date', 'amount', 'category', 'description']]

        return {
            'greeting': get_greeting(date),
            'cards': cards,
            'top_transactions': top_trans.to_dict('records') if not top_trans.empty else [],
            'currency_rates': get_currency_rates(),
            'stock_prices': get_stock_prices()
        }
    except Exception as e:
        logger.error(f"Ошибка при генерации данных: {str(e)}")
        raise


def get_currency_rates() -> list:
    """Возвращает текущие курсы валют (заглушка)."""
    return [
        {'currency': 'USD', 'rate': 75.50},
        {'currency': 'EUR', 'rate': 85.20}
    ]


def get_stock_prices() -> list:
    """Возвращает текущие цены акций (заглушка)."""
    return [
        {'stock': 'AAPL', 'price': 150.12},
        {'stock': 'GOOGL', 'price': 2742.39}
    ]