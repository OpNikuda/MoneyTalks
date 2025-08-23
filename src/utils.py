"""
Утилиты и вспомогательные функции для работы с транзакциями.
Включает функции загрузки данных, фильтрации, расчета кешбэка и другие утилиты.
"""

import pandas as pd
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
from typing import Union, List, Dict, Any, Tuple
import json
import re


def setup_logging() -> None:
    """
    Настраивает логирование приложения с ротацией файлов.

    Returns:
        None
    """
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
    """
    Загружает транзакции из Excel или CSV файла.

    Args:
        file_path: Путь к файлу с транзакциями

    Returns:
        DataFrame с загруженными транзакциями
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Загрузка файла: {file_path}")

    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.csv'):
            # Указываем явно параметры для CSV
            df = pd.read_csv(
                file_path,
                decimal=',',
                thousands=' ',
                parse_dates=['Дата операции'],
                dayfirst=True
            )
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
            'Кэшбэк': 'cashback',
            'Категория': 'category',
            'MCC': 'mcc',
            'Описание': 'description',
            'Бонусы (включая кэшбэк)': 'bonuses',
            'Округление на инвесткопилку': 'rounding',
            'Сумма операции с округлением': 'rounded_amount'
        }

        # Переименовываем только те столбцы, которые есть в файле
        existing_columns = [col for col in column_mapping.keys() if col in df.columns]
        df.rename(columns={col: column_mapping[col] for col in existing_columns}, inplace=True)

        # Преобразуем amount в числовой формат
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'].astype(str).str.replace(',', '.'), errors='coerce')

        logger.info(f"Загружено {len(df)} транзакций")
        return df

    except Exception as e:
        logger.exception("Ошибка загрузки данных")
        raise


def filter_transactions_by_date(df: pd.DataFrame, start_date: Union[str, datetime],
                                end_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Фильтрует транзакции по заданному диапазону дат.

    Args:
        df: DataFrame с транзакциями
        start_date: Начальная дата диапазона
        end_date: Конечная дата диапазона

    Returns:
        Отфильтрованный DataFrame
    """
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
    """
    Рассчитывает кешбэк 1% от суммы.

    Args:
        amount: Сумма для расчета кешбэка

    Returns:
        Размер кешбэка
    """
    return max(0, amount) * 0.01


def get_month_range(date: Union[str, datetime]) -> Tuple[datetime, datetime]:
    """
    Возвращает первый и последний день месяца для указанной даты.

    Args:
        date: Дата для определения диапазона месяца

    Returns:
        Кортеж (первый_день_месяца, последний_день_месяца)
    """
    if isinstance(date, str):
        date = pd.to_datetime(date)
    first_day = date.replace(day=1)
    next_month = first_day + timedelta(days=32)
    last_day = next_month.replace(day=1) - timedelta(days=1)
    return first_day, last_day


def mask_card_number(number: str) -> str:
    """
    Маскирует номер карты, оставляя только последние 4 цифры.

    Args:
        number: Номер карты для маскировки

    Returns:
        Замаскированный номер карты
    """
    if number is None or number == "":
        return ""
    return f"****{str(number)[-4:]}"


def detect_phone_numbers(text: str) -> List[str]:
    """
    Обнаруживает номера телефонов в тексте.

    Args:
        text: Текст для поиска номеров телефонов

    Returns:
        Список найденных номеров телефонов
    """
    if text is None:
        return []

    # Улучшенное регулярное выражение
    pattern = r'(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'
    return re.findall(pattern, str(text))


def save_to_json(data: Dict[str, Any], filename: str) -> None:
    """
    Сохраняет данные в JSON файл.

    Args:
        data: Данные для сохранения
        filename: Имя файла

    Returns:
        None
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_weekend(date: datetime) -> bool:
    """
    Проверяет, является ли день выходным.

    Args:
        date: Дата для проверки

    Returns:
        True если выходной, иначе False
    """
    return date.weekday() >= 5