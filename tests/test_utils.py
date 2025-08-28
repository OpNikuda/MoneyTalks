from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from src.utils import (
    calculate_cashback,
    filter_transactions_by_date,
    get_month_range,
    is_weekend,
    load_transactions,
    mask_card_number,
    save_to_json,
)


@patch('pandas.read_excel')
def test_load_transactions_xlsx_column_mapping(mock_read_excel):
    """Тест маппинга колонок для XLSX"""
    mock_df = pd.DataFrame({
        'Дата операции': ['2023-01-01'],
        'Сумма операции': ['1000,50'],
        'Категория': ['Еда'],
        'Неизвестная колонка': ['test']  # Не должна быть переименована
    })
    mock_read_excel.return_value = mock_df

    result = load_transactions('test.xlsx')

    # Проверяем переименованные колонки
    assert 'date' in result.columns
    assert 'amount' in result.columns
    assert 'category' in result.columns
    assert 'Неизвестная колонка' in result.columns  # Осталась как есть


def test_filter_transactions_missing_date_column():
    """Тест фильтрации при отсутствии колонки date"""
    df = pd.DataFrame({
        'amount': [100, 200],
        'category': ['food', 'transport']
    })

    with pytest.raises(ValueError, match="DataFrame должен содержать колонку 'date'"):
        filter_transactions_by_date(df, datetime(2023, 1, 1), datetime(2023, 1, 31))


def test_calculate_cashback_edge_cases():
    """Тест расчета кешбэка с граничными значениями"""
    assert calculate_cashback(0.0) == 0.0
    assert calculate_cashback(-100.0) == 0.0
    assert calculate_cashback(100.0) == 1.0
    assert calculate_cashback(999.99) == 9.9999


def test_mask_card_number_edge_cases():
    """Тест маскировки номера карты с граничными случаями"""
    assert mask_card_number(None) == ""
    assert mask_card_number("") == ""
    assert mask_card_number(1234567890123456) == "****3456"  # Числовой ввод


def test_get_month_range():
    """Тест получения диапазона месяца"""
    test_date = datetime(2023, 2, 15)
    first_day, last_day = get_month_range(test_date)

    assert first_day == datetime(2023, 2, 1)
    assert last_day == datetime(2023, 2, 28)  # Февраль 2023 не високосный


def test_is_weekend():
    """Тест проверки выходных дней"""
    assert is_weekend(datetime(2023, 1, 7))  # Суббота
    assert is_weekend(datetime(2023, 1, 8))  # Воскресенье
    assert not is_weekend(datetime(2023, 1, 9))  # Понедельник


@patch('builtins.open')
@patch('json.dump')
def test_save_to_json_success(mock_json_dump, mock_open):
    """Тест успешного сохранения в JSON"""
    test_data = {'key': 'value'}

    save_to_json(test_data, 'test.json')

    mock_open.assert_called_once_with('test.json', 'w', encoding='utf-8')
    mock_json_dump.assert_called_once_with(test_data, mock_open.return_value.__enter__.return_value,
                                           ensure_ascii=False, indent=2)


@patch('builtins.open')
@patch('src.utils.logger')
def test_save_to_json_error(mock_logger, mock_open):
    """Тест ошибки при сохранении в JSON"""
    mock_open.side_effect = Exception("File error")

    with pytest.raises(Exception):
        save_to_json({'test': 'data'}, 'test.json')

    mock_logger.error.assert_called()
