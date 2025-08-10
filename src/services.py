import pandas as pd
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def analyze_cashback_categories(
        data: List[Dict[str, Any]],
        year: int,
        month: int
) -> Dict[str, float]:
    """
    Анализирует выгодные категории для повышенного кешбэка.

    Args:
        data: Список транзакций
        year: Год анализа
        month: Месяц анализа

    Returns:
        Словарь с категориями и суммами потенциального кешбэка
    """
    try:
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])

        # Фильтрация по месяцу и тратам
        filtered = df[
            (df['date'].dt.year == year) &
            (df['date'].dt.month == month) &
            (df['amount'] < 0)
            ]

        # Расчет кешбэка по категориям (5% от суммы)
        result = (
            filtered.groupby('category')['amount']
            .apply(lambda x: x.abs().sum() * 0.05)
            .to_dict()
        )

        return result

    except Exception as e:
        logger.error(f"Error in analyze_cashback_categories: {str(e)}")
        return {}


def investment_bank(
        month: str,
        transactions: List[Dict[str, Any]],
        limit: int
) -> float:

    try:
        year, month = map(int, month.split('-'))
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])

        # Фильтрация по месяцу и тратам
        filtered = df[
            (df['date'].dt.year == year) &
            (df['date'].dt.month == month) &
            (df['amount'] < 0)
            ]

        # Расчет округления с ограничением
        roundup = filtered['amount'].apply(
            lambda x: min(limit, (abs(x) // limit + 1) * limit - abs(x))
        )

        return roundup.sum()

    except Exception as e:
        logger.error(f"Error in investment_bank: {str(e)}")
        return 0.0


def simple_search(
        query: str,
        transactions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    try:
        return [
            t for t in transactions
            if query.lower() in str(t.get('description', '')).lower() or
               query.lower() in str(t.get('category', '')).lower()
        ]
    except Exception as e:
        logger.error(f"Error in simple_search: {str(e)}")
        return []