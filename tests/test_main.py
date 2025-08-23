import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd
from src.main import main_function, get_greeting, generate_home_data


def test_get_greeting():
    """Тест приветствия по времени суток"""
    assert get_greeting(datetime(2023, 1, 1, 6, 0)) == "Доброе утро"
    assert get_greeting(datetime(2023, 1, 1, 13, 0)) == "Добрый день"
    assert get_greeting(datetime(2023, 1, 1, 20, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2023, 1, 1, 2, 0)) == "Доброй ночи"


@patch('src.main.filter_transactions_by_date')
def test_generate_home_data(mock_filter):
    """Тест генерации данных для домашней страницы"""
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

    assert 'cards' in result
    assert 'top_transactions' in result
    assert 'currency_rates' in result
    assert 'stock_prices' in result
    assert len(result['cards']) == 2  # Две уникальные карты


@patch('argparse.ArgumentParser.parse_args')
@patch('src.main.load_transactions')
@patch('src.main.generate_home_data')
@patch('builtins.print')
def test_main_function_success(mock_print, mock_generate, mock_load, mock_parse_args):
    """Тест успешного выполнения main функции"""
    # Mock аргументов
    mock_args = MagicMock()
    mock_args.file = 'test.csv'
    mock_args.date = '2023-01-01'
    mock_parse_args.return_value = mock_args

    # Mock данных
    mock_df = MagicMock()
    mock_load.return_value = mock_df
    mock_generate.return_value = {'test': 'data'}

    main_function()

    mock_print.assert_called()
    mock_load.assert_called_with('test.csv')


@patch('argparse.ArgumentParser.parse_args')
@patch('src.main.load_transactions')
def test_main_function_file_not_found(mock_load, mock_parse_args):
    """Тест ошибки при отсутствии файла"""
    # Mock аргументов
    mock_args = MagicMock()
    mock_args.file = '/nonexistent/file.csv'
    mock_args.date = '2023-01-01'
    mock_parse_args.return_value = mock_args

    # Mock ошибки загрузки
    mock_load.side_effect = FileNotFoundError("File not found")

    with pytest.raises(FileNotFoundError):
        main_function()