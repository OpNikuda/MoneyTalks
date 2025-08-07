import pandas as pd
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
from typing import Union, List, Dict, Any
import json
import re


# Настройка логирования для всех модулей
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                'transactions.log',
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )
    logging.captureWarnings(True)


setup_logging()


def load_transactions(file_path: str) -> pd.DataFrame:
    logger = logging.getLogger(__name__)
    logger.info(f"Загрузка файла: {file_path}")

    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, decimal=',', thousands=' ')
        else:
            raise ValueError("Поддерживаются только .xlsx или .csv")

        column_mapping = {
            'Дата операции': 'date',
            'Дата платежа': 'payment_date',
            'Номер карты': 'card_last_digits',
            'Статус': 'status',
            'Сумма операции': 'amount',
            'Валюта операции': 'currency',
            'Сумма платежа': 'payment_amount',
            'Валюта платежа': 'payment_currency',
            'Кешбэк': 'cashback',
            'Категория': 'category',
            'MCC': 'mcc',
            'Описание': 'description',
            'Бонусы (включая кешбэк)': 'bonuses',
            'Округление на Инвесткопилку': 'rounding',
            'Сумма операции с округлением': 'rounded_amount'
        }

        df.rename(columns=column_mapping, inplace=True)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)
        df['amount'] = df['amount'].astype(float)

        logger.info(f"Загружено {len(df)} транзакций")
        return df

    except Exception as e:
        logger.exception("Ошибка загрузки данных")
        raise


def filter_transactions_by_date(df: pd.DataFrame, start_date: Union[str, datetime],
                                end_date: Union[str, datetime]) -> pd.DataFrame:
    logger = logging.getLogger(__name__)
    try:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        filtered_df = df.loc[mask].copy()
        logger.info(f"Отфильтровано {len(filtered_df)} транзакций")
        return filtered_df
    except Exception as e:
        logger.exception("Ошибка фильтрации по дате")
        raise


def calculate_cashback(amount: float) -> float:
    return max(0, amount) * 0.01


def get_month_range(date: Union[str, datetime]) -> tuple[datetime, datetime]:
    if isinstance(date, str):
        date = pd.to_datetime(date)
    first_day = date.replace(day=1)
    next_month = first_day + timedelta(days=32)
    last_day = next_month.replace(day=1) - timedelta(days=1)
    return first_day, last_day


def mask_card_number(number: str) -> str:
    return f"****{str(number)[-4:]}" if pd.notna(number) else ""


def detect_phone_numbers(text: str) -> list:
    return re.findall(r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', str(text))


def save_to_json(data: dict, filename: str):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_weekend(date: datetime) -> bool:
    return date.weekday() >= 5