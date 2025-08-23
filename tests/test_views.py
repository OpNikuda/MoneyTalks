from src.views import (
    get_currency_rates_fallback,
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
