import pytest
import pandas as pd
from unittest.mock import patch
from datetime import datetime
from src.views import generate_home_data, get_currency_rates, get_stock_prices


@patch('src.views.filter_transactions_by_date')
def test_generate_home_data(mock_filter):
    """Тест генерации домашних данных"""
    # Создаем тестовый DataFrame
    test_df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=10),
        'amount': [-100, -200, 300, -400, -500, 600, -700, -800, 900, -1000],
        'card_last_digits': ['1234', '5678', '1234', '5678', '1234', '5678', '1234', '5678', '1234', '5678'],
        'category': ['food', 'transport', 'food', 'transport', 'food', 'transport', 'food', 'transport', 'food',
                     'transport'],
        'description': ['test1', 'test2', 'test3', 'test4', 'test5', 'test6', 'test7', 'test8', 'test9', 'test10']
    })

    mock_filter.return_value = test_df

    result = generate_home_data(test_df, '2023-01-15')

    # Проверяем структуру результата
    assert 'cards' in result
    assert 'top_transactions' in result
    assert 'currency_rates' in result
    assert 'stock_prices' in result

    # Проверяем количество карт
    assert len(result['cards']) == 2

    # Дополнительные проверки данных
    assert isinstance(result['cards'], list)
    for card in result['cards']:
        assert 'last_digits' in card
        assert 'total_spent' in card
        assert 'cashback' in card
        # Исправленная проверка для numpy типов
        assert hasattr(card['total_spent'], 'real')  # Проверяем, что это числовой тип
        assert hasattr(card['cashback'], 'real')  # Проверяем, что это числовой тип


