import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch

from src.reports import (
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)


@pytest.fixture
def sample_transactions():
    """Фикстура с тестовыми транзакциями"""
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
    n = len(dates)

    return pd.DataFrame({
        'date': dates,
        'amount': np.random.uniform(-1000, -10, n),  # Только отрицательные значения (траты)
        'category': np.random.choice(['food', 'transport', 'entertainment', 'utilities'], n),
        'description': [f'Transaction {i}' for i in range(n)]
    })


@pytest.fixture
def mock_load_transactions(sample_transactions):
    """Мок для функции загрузки транзакций"""
    with patch('src.reports.load_transactions') as mock:
        mock.return_value = sample_transactions
        yield mock


def test_spending_by_category_basic(mock_load_transactions):
    """Тест базовой функциональности spending_by_category"""
    result = spending_by_category(
        'dummy_path.csv',
        category='food',
        skip_save=True
    )

    mock_load_transactions.assert_called_once_with('dummy_path.csv')
    assert isinstance(result, pd.DataFrame)
    assert set(result.columns) == {'Месяц', 'Категория', 'Сумма'}
    assert all(result['Сумма'] > 0)


def test_spending_by_category_nonexistent_category(mock_load_transactions):
    """Тест spending_by_category для несуществующей категории"""
    # Мокаем возврат данных без нужной категории
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
    mock_transactions = pd.DataFrame({
        'date': dates,
        'amount': [-100] * len(dates),
        'category': ['other'] * len(dates)
    })
    mock_load_transactions.return_value = mock_transactions

    result = spending_by_category(
        'dummy_path.csv',
        category='nonexistent',
        skip_save=True
    )

    assert len(result) == 0
    assert set(result.columns) == {'Месяц', 'Категория', 'Сумма'}


def test_spending_by_category_date_filter(mock_load_transactions):
    """Тест фильтрации по дате в spending_by_category"""
    test_date = '2024-03-15'

    result = spending_by_category(
        'dummy_path.csv',
        category='food',
        date=test_date,
        skip_save=True
    )

    # Проверяем, что данные ограничены последними 3 месяцами
    if len(result) > 0:
        max_date = pd.to_datetime(test_date)
        min_date = max_date - pd.DateOffset(months=3)
        result_months = result['Месяц'].dt.to_timestamp()
        assert all(min_date <= month <= max_date for month in result_months)


def test_spending_by_weekday_empty_data():
    """Тест spending_by_weekday с пустыми данными"""
    with patch('src.reports.load_transactions') as mock_load:
        mock_load.return_value = pd.DataFrame(columns=['date', 'amount'])

        result = spending_by_weekday(
            'dummy_path.csv',
            skip_save=True
        )

        assert len(result) == 0
        assert set(result.columns) == {'День_недели', 'Средний_расход'}


def test_spending_by_category_missing_category_column():
    """Тест обработки отсутствия колонки category"""
    with patch('src.reports.load_transactions') as mock_load:
        # Создаем DataFrame без колонки category
        mock_transactions = pd.DataFrame({
            'date': [datetime(2024, 1, 1)],
            'amount': [-100],
            'description': ['test']
        })
        mock_load.return_value = mock_transactions

        result = spending_by_category(
            'dummy_path.csv',
            category='food',
            skip_save=True
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert set(result.columns) == {'Месяц', 'Категория', 'Сумма'}


def test_spending_functions_with_positive_amounts():
    """Тест фильтрации положительных сумм (доходов)"""
    with patch('src.reports.load_transactions') as mock_load:
        # Создаем данные только с положительными суммами (доходы)
        dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='D')
        mock_transactions = pd.DataFrame({
            'date': dates,
            'amount': [100] * len(dates),  # Положительные значения
            'category': ['salary'] * len(dates)
        })
        mock_load.return_value = mock_transactions

        # Все функции должны вернуть пустые результаты
        result1 = spending_by_category('dummy.csv', category='salary', skip_save=True)
        result2 = spending_by_weekday('dummy.csv', skip_save=True)
        result3 = spending_by_workday('dummy.csv', skip_save=True)

        assert len(result1) == 0
        assert len(result2) == 0
        assert len(result3) == 0
