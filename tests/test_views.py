from unittest.mock import MagicMock, patch

import requests

from src.views import (
    get_currency_rates,
    get_currency_rates_fallback,
    get_stock_prices,
    get_stock_prices_fallback,
)


def test_get_currency_rates_fallback_returns_correct_data():
    """Тест заглушки курсов валют"""
    result = get_currency_rates_fallback()

    assert isinstance(result, list)
    assert len(result) == 4

    expected_currencies = ['USD', 'EUR', 'GBP', 'JPY']
    for item in result:
        assert 'currency' in item
        assert 'rate' in item
        assert item['currency'] in expected_currencies
        assert isinstance(item['rate'], float)


def test_get_stock_prices_fallback_returns_correct_data():
    """Тест заглушки цен акций"""
    result = get_stock_prices_fallback()

    assert isinstance(result, list)
    assert len(result) == 4

    expected_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    for item in result:
        assert 'stock' in item
        assert 'price' in item
        assert item['stock'] in expected_stocks
        assert isinstance(item['price'], float)


@patch('src.views.requests.get')
@patch('src.views.CURRENCY_API_KEY', 'test_key')
@patch('src.views.CURRENCY_API_URL', 'http://test-api.com')
def test_get_currency_rates_api_error(mock_get):
    """Тест обработки ошибки API курсов валют"""
    mock_get.side_effect = requests.exceptions.RequestException("API error")

    result = get_currency_rates()

    # Должен вернуть заглушку
    assert len(result) == 4
    assert any(item['currency'] == 'USD' for item in result)


@patch('src.views.requests.get')
@patch('src.views.CURRENCY_API_KEY', 'test_key')
@patch('src.views.CURRENCY_API_URL', 'http://test-api.com')
def test_get_currency_rates_invalid_response(mock_get):
    """Тест обработки невалидного ответа API"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'invalid': 'data'}  # Нет ключа 'rates'
    mock_get.return_value = mock_response

    result = get_currency_rates()

    # Должен вернуть заглушку
    assert len(result) == 4
    assert any(item['currency'] == 'USD' for item in result)


@patch('src.views.requests.get')
@patch('src.views.STOCK_API_KEY', 'test_key')
@patch('src.views.STOCK_API_URL', 'http://test-api.com')
def test_get_stock_prices_success(mock_get):
    """Тест успешного получения цен акций из API"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'Global Quote': {
            'AAPL': {'05. price': '150.12'},
            'GOOGL': {'05. price': '2742.39'},
            'MSFT': {'05. price': '305.50'},
            'TSLA': {'05. price': '210.75'}
        }
    }
    mock_get.return_value = mock_response

    result = get_stock_prices()

    assert len(result) == 4
    assert any(item['stock'] == 'AAPL' for item in result)
    mock_get.assert_called_once()


@patch('src.views.requests.get')
@patch('src.views.STOCK_API_KEY', 'test_key')
@patch('src.views.STOCK_API_URL', 'http://test-api.com')
def test_get_stock_prices_api_error(mock_get):
    """Тест обработки ошибки API цен акций"""
    mock_get.side_effect = requests.exceptions.RequestException("API error")

    result = get_stock_prices()

    # Должен вернуть заглушку
    assert len(result) == 4
    assert any(item['stock'] == 'AAPL' for item in result)


@patch('src.views.requests.get')
@patch('src.views.STOCK_API_KEY', 'test_key')
@patch('src.views.STOCK_API_URL', 'http://test-api.com')
def test_get_stock_prices_invalid_response(mock_get):
    """Тест обработки невалидного ответа API акций"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'invalid': 'data'}  # Нет ключа 'Global Quote'
    mock_get.return_value = mock_response

    result = get_stock_prices()

    # Должен вернуть заглушку
    assert len(result) == 4
    assert any(item['stock'] == 'AAPL' for item in result)


@patch('src.views.requests.get')
@patch('src.views.STOCK_API_KEY', 'test_key')
@patch('src.views.STOCK_API_URL', 'http://test-api.com')
def test_get_stock_prices_missing_price_key(mock_get):
    """Тест обработки отсутствия ключа цены в ответе API"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'Global Quote': {
            'AAPL': {'wrong_key': '150.12'},  # Нет ключа '05. price'
            'GOOGL': {'05. price': '2742.39'}
        }
    }
    mock_get.return_value = mock_response

    result = get_stock_prices()

    # Должен вернуть только валидные акции или заглушку
    assert len(result) <= 4


@patch('src.views.CURRENCY_API_KEY', None)
def test_get_currency_rates_no_credentials():
    """Тест получения курсов валют без настроенных учетных данных"""
    result = get_currency_rates()
    assert len(result) == 4  # Должен использовать заглушку


@patch('src.views.STOCK_API_KEY', None)
def test_get_stock_prices_no_credentials():
    """Тест получения цен акций без настроенных учетных данных"""
    result = get_stock_prices()
    assert len(result) == 4  # Должен использовать заглушку


@patch('src.views.CURRENCY_API_URL', None)
def test_get_currency_rates_no_api_url():
    """Тест получения курсов валют без настроенного URL API"""
    result = get_currency_rates()
    assert len(result) == 4  # Должен использовать заглушку


@patch('src.views.STOCK_API_URL', None)
def test_get_stock_prices_no_api_url():
    """Тест получения цен акций без настроенного URL API"""
    result = get_stock_prices()
    assert len(result) == 4  # Должен использовать заглушку
