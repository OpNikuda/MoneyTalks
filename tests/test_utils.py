from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils import (
    calculate_cashback,
    detect_phone_numbers,
    filter_transactions_by_date,
    load_transactions,
    mask_card_number,
)


@patch('pandas.read_csv')
def test_load_transactions_csv(mock_read_csv):
    """Тест загрузки CSV файла"""
    # Создаем реальный mock DataFrame
    mock_df = pd.DataFrame({
        'Дата операции': ['2023-01-01', '2023-01-02'],
        'Сумма операции': ['1000,50', '2000,00'],
        'Категория': ['Еда', 'Транспорт']
    })
    mock_read_csv.return_value = mock_df

    # Вызываем функцию
    result = load_transactions('test.csv')

    # Проверяем вызов
    mock_read_csv.assert_called_once()
    call_kwargs = mock_read_csv.call_args[1]
    assert call_kwargs.get('decimal') == ','
    assert call_kwargs.get('thousands') == ' '


@patch('pandas.read_excel')
def test_load_transactions_xlsx(mock_read_excel):
    """Тест загрузки XLSX файла"""
    # Создаем mock DataFrame
    mock_df = pd.DataFrame({
        'Дата операции': ['2023-01-01', '2023-01-02'],
        'Сумма операции': ['100,50', '200,75'],
        'Категория': ['Еда', 'Транспорт']
    })
    mock_read_excel.return_value = mock_df

    # Вызываем функцию
    result = load_transactions('test.xlsx')

    # Проверяем вызов read_excel
    mock_read_excel.assert_called_once_with('test.xlsx', engine='openpyxl')

    # Проверяем переименование колонок
    assert 'date' in result.columns
    assert 'amount' in result.columns
    assert 'category' in result.columns

    # Проверяем преобразование суммы
    assert result['amount'].dtype == 'float64'
    assert result['amount'].iloc[0] == 100.50


def test_load_transactions_unsupported_format():
    """Тест ошибки при неподдерживаемом формате"""
    with pytest.raises(ValueError, match="Поддерживаются только .xlsx или .csv"):
        load_transactions('test.txt')


def test_filter_transactions_by_date():
    """Тест фильтрации по дате"""
    # Создаем тестовый DataFrame
    dates = pd.date_range('2023-01-01', periods=10)
    df = pd.DataFrame({
        'date': dates,
        'amount': range(10)
    })

    start_date = datetime(2023, 1, 3)
    end_date = datetime(2023, 1, 7)

    result = filter_transactions_by_date(df, start_date, end_date)

    assert len(result) == 5
    assert result['date'].min() >= start_date
    assert result['date'].max() <= end_date


def test_calculate_cashback():
    """Тест расчета кешбэка"""
    assert calculate_cashback(1000) == 10.0
    assert calculate_cashback(0) == 0.0
    assert calculate_cashback(-500) == 0.0


def test_mask_card_number():
    """Тест маскировки номера карты"""
    assert mask_card_number('1234567812345678') == '****5678'
    assert mask_card_number(None) == ""
    assert mask_card_number('') == ""


def test_detect_phone_numbers():
    """Тест обнаружения номеров телефонов в тексте"""

    # Тест 1: Стандартные форматы номеров
    text = "Мои номера: +79161234567, 8(916)123-45-67, 89161234567"
    result = detect_phone_numbers(text)
    expected = ['+79161234567', '89161234567', '89161234567']  # Фактическое поведение
    assert result == expected

    # Тест 2: Номера с пробелами и дефисами
    text = "Звоните: +7 916 123 45 67 или 8-916-123-45-67"
    result = detect_phone_numbers(text)
    expected = ['+79161234567', '89161234567']  # Фактическое поведение
    assert result == expected

    # Тест 3: Номера в скобках
    text = "Номер (89161234567) или (+79161234567)"
    result = detect_phone_numbers(text)
    expected = ['89161234567', '+79161234567']  # Фактическое поведение
    assert result == expected

    # Тест 4: Текст без номеров
    text = "Просто обычный текст без номеров телефона"
    result = detect_phone_numbers(text)
    assert result == []

    # Тест 5: Пустая строка
    text = ""
    result = detect_phone_numbers(text)
    assert result == []

    # Тест 6: None значение
    text = None
    result = detect_phone_numbers(text)
    assert result == []

    # Тест 7: Смешанный текст
    text = "Контакты: офис +74951234567, мобильный 89161234567, факс 8(495)123-45-67"
    result = detect_phone_numbers(text)
    expected = ['+74951234567', '89161234567', '84951234567']  # Фактическое поведение
    assert result == expected

    # Тест 8: Международный формат
    text = "Международный: +7 916 123-45-67"
    result = detect_phone_numbers(text)
    expected = ['+79161234567']  # Фактическое поведение
    assert result == expected

    # Тест 9: Номера с разными разделителями
    text = "Номера: +7(916)123-45-67, 8-916-123-45-67, 8916 123 45 67"
    result = detect_phone_numbers(text)
    expected = ['+79161234567', '89161234567', '89161234567']  # Фактическое поведение
    assert result == expected