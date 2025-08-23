"""
Модуль представлений для генерации данных отображения.
Содержит функции для подготовки данных для UI.
"""

from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import requests
import os
import logging
from dotenv import load_dotenv
from src.utils import (
    filter_transactions_by_date,
    calculate_cashback,
    mask_card_number
)

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

# Получение конфигурации из .env
CURRENCY_API_KEY = os.getenv('CURRENCY_API_KEY')
STOCK_API_KEY = os.getenv('STOCK_API_KEY')
CURRENCY_API_URL = os.getenv('CURRENCY_API_URL')
STOCK_API_URL = os.getenv('STOCK_API_URL')


def get_currency_rates() -> List[Dict[str, Any]]:
    """
    Возвращает курсы валют из API или заглушку.

    Returns:
        Список словарей с валютами и курсами
    """
    try:
        if not CURRENCY_API_KEY or not CURRENCY_API_URL:
            logger.warning("Currency API credentials not configured, using fallback")
            return get_currency_rates_fallback()

        params = {'apikey': CURRENCY_API_KEY}
        response = requests.get(CURRENCY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        rates_data = response.json()

        if 'rates' in rates_data:
            major_currencies = ['EUR', 'GBP', 'JPY', 'CNY', 'RUB']
            return [
                {'currency': curr, 'rate': round(rates_data['rates'][curr], 2)}
                for curr in major_currencies if curr in rates_data['rates']
            ]

        return get_currency_rates_fallback()

    except requests.exceptions.RequestException as e:
        logger.error(f"Currency API request failed: {e}")
        return get_currency_rates_fallback()
    except Exception as e:
        logger.error(f"Error processing currency rates: {e}")
        return get_currency_rates_fallback()

def get_currency_rates_fallback() -> List[Dict[str, Any]]:
    """Заглушка для курсов валют при недоступности API."""
    return [
        {'currency': 'USD', 'rate': 75.50},
        {'currency': 'EUR', 'rate': 85.20},
        {'currency': 'GBP', 'rate': 95.75},
        {'currency': 'JPY', 'rate': 0.68}
    ]

def get_stock_prices() -> List[Dict[str, Any]]:
    """
    Возвращает цены акций из API или заглушку.

    Returns:
        Список словарей с акциями и ценами
    """
    try:
        if not STOCK_API_KEY or not STOCK_API_URL:
            logger.warning("Stock API credentials not configured, using fallback")
            return get_stock_prices_fallback()

        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        params = {
            'apikey': STOCK_API_KEY,
            'function': 'GLOBAL_QUOTE',
            'symbol': ','.join(symbols)
        }

        response = requests.get(STOCK_API_URL, params=params, timeout=10)
        response.raise_for_status()
        prices_data = response.json()

        stocks = []
        for symbol in symbols:
            quote_key = f'Global Quote'
            if quote_key in prices_data and symbol in prices_data[quote_key]:
                stock_data = prices_data[quote_key][symbol]
                if '05. price' in stock_data:
                    stocks.append({
                        'stock': symbol,
                        'price': round(float(stock_data['05. price']), 2)
                    })

        return stocks if stocks else get_stock_prices_fallback()

    except requests.exceptions.RequestException as e:
        logger.error(f"Stock API request failed: {e}")
        return get_stock_prices_fallback()
    except Exception as e:
        logger.error(f"Error processing stock prices: {e}")
        return get_stock_prices_fallback()

def get_stock_prices_fallback() -> List[Dict[str, Any]]:
    """Заглушка для цен акций при недоступности API."""
    return [
        {'stock': 'AAPL', 'price': 150.12},
        {'stock': 'GOOGL', 'price': 2742.39},
        {'stock': 'MSFT', 'price': 305.50},
        {'stock': 'TSLA', 'price': 210.75}
    ]