import pytest
import pandas as pd
from datetime import datetime
from src.services import analyze_cashback_categories, investment_bank, simple_search


def test_analyze_cashback_categories():
    """Тест анализа кешбэк категорий"""
    # Создаем тестовые данные
    test_data = [
        {'date': datetime(2023, 1, 1), 'amount': -1000, 'category': 'food'},
        {'date': datetime(2023, 1, 2), 'amount': -2000, 'category': 'transport'},
        {'date': datetime(2023, 1, 3), 'amount': -1500, 'category': 'food'},
        {'date': datetime(2023, 2, 1), 'amount': -500, 'category': 'food'},  # Другой месяц
    ]

    result = analyze_cashback_categories(test_data, 2023, 1)

    assert isinstance(result, dict)
    assert 'food' in result
    assert 'transport' in result
    assert result['food'] == 125.0  # (1000 + 1500) * 0.05


def test_investment_bank():
    """Тест инвестиционного копилка"""
    # Создаем тестовые данные
    test_data = [
        {'date': datetime(2023, 1, 1), 'amount': -123},
        {'date': datetime(2023, 1, 2), 'amount': -456},
        {'date': datetime(2023, 2, 1), 'amount': -789},  # Другой месяц
    ]

    result = investment_bank('2023-01', test_data, 100)

    # Округление для 123: 100 - 23 = 77
    # Округление для 456: 100 - 56 = 44
    assert result == 121.0


def test_simple_search():
    """Тест простого поиска"""
    # Создаем тестовые данные
    test_data = [
        {'description': 'Магазин Пятерочка', 'category': 'Продукты'},
        {'description': 'Такси Яндекс', 'category': 'Транспорт'},
        {'description': 'Кафе Starbucks', 'category': 'Рестораны'},
    ]

    result = simple_search('Пятерочка', test_data)

    assert len(result) == 1
    assert result[0]['description'] == 'Магазин Пятерочка'