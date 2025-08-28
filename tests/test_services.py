from datetime import datetime

from src.services import analyze_cashback_categories, investment_bank, simple_search


def test_analyze_cashback_categories():
    """Тест анализа кешбэк категорий"""
    # Создаем тестовые данные
    test_data = [
        {'date': datetime(2025, 1, 1), 'amount': -1000, 'category': 'food'},
        {'date': datetime(2025, 1, 2), 'amount': -2000, 'category': 'transport'},
        {'date': datetime(2025, 1, 3), 'amount': -1500, 'category': 'food'},
        {'date': datetime(2025, 2, 1), 'amount': -500, 'category': 'food'},  # Другой месяц
    ]

    result = analyze_cashback_categories(test_data, 2025, 1)

    assert isinstance(result, dict)
    assert 'food' in result
    assert 'transport' in result
    assert result['food'] == 125.0  # (1000 + 1500) * 0.05


def test_analyze_cashback_categories_empty_data():
    """Тест анализа кешбэк категорий с пустыми данными"""
    result = analyze_cashback_categories([], 2025, 1)
    assert result == {}


def test_analyze_cashback_categories_no_negative_amounts():
    """Тест анализа кешбэк категорий без отрицательных сумм"""
    test_data = [
        {'date': datetime(2025, 1, 1), 'amount': 1000, 'category': 'food'},  # Положительная сумма
        {'date': datetime(2025, 1, 2), 'amount': 2000, 'category': 'transport'},
    ]

    result = analyze_cashback_categories(test_data, 2025, 1)
    assert result == {}


def test_analyze_cashback_categories_error_handling():
    """Тест обработки ошибок в analyze_cashback_categories"""
    # Передаем некорректные данные
    result = analyze_cashback_categories('invalid_data', 911, 1)
    assert result == {}


def test_investment_bank():
    """Тест инвестиционного копилка"""
    # Создаем тестовые данные
    test_data = [
        {'date': datetime(2025, 1, 1), 'amount': -123},
        {'date': datetime(2025, 1, 2), 'amount': -456},
        {'date': datetime(2025, 2, 1), 'amount': -789},  # Другой месяц
    ]

    result = investment_bank('2025-01', test_data, 100)

    # Округление для 123: 100 - 23 = 77
    # Округление для 456: 100 - 56 = 44
    assert result == 121.0


def test_investment_bank_empty_data():
    """Тест инвестиционного копилка с пустыми данными"""
    result = investment_bank('2025-01', [], 100)
    assert result == 0.0


def test_investment_bank_no_negative_amounts():
    """Тест инвестиционного копилка без отрицательных сумм"""
    test_data = [
        {'date': datetime(2025, 1, 1), 'amount': 123},  # Положительная сумма
        {'date': datetime(2025, 1, 2), 'amount': 456},
    ]

    result = investment_bank('2025-01', test_data, 100)
    assert result == 0.0


def test_investment_bank_limit_zero():
    """Тест инвестиционного копилка с лимитом 0"""
    test_data = [
        {'date': datetime(2023, 1, 1), 'amount': -123},
    ]

    result = investment_bank('2023-01', test_data, 0)
    assert result == 0.0


def test_investment_bank_error_handling():
    """Тест обработки ошибок в investment_bank"""
    result = investment_bank('invalid-date', 'invalid_data', 100)
    assert result == 0.0


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


def test_simple_search_by_category():
    """Тест поиска по категории"""
    test_data = [
        {'description': 'Магазин Ашан', 'category': 'Продукты'},
        {'description': 'Такси Убер', 'category': 'Транспорт'},
    ]

    result = simple_search('Продукты', test_data)
    assert len(result) == 1
    assert result[0]['category'] == 'Продукты'


def test_simple_search_case_insensitive():
    """Тест поиска без учета регистра"""
    test_data = [
        {'description': 'Магазин ПЯТЕРОЧКА', 'category': 'Продукты'},
    ]

    result = simple_search('пятерочка', test_data)
    assert len(result) == 1


def test_simple_search_multiple_results():
    """Тест поиска с несколькими результатами"""
    test_data = [
        {'description': 'Пятерочка магазин', 'category': 'Продукты'},
        {'description': 'Пятерочка доставка', 'category': 'Продукты'},
        {'description': 'Ашан', 'category': 'Продукты'},
    ]

    result = simple_search('Пятерочка', test_data)
    assert len(result) == 2


def test_simple_search_no_results():
    """Тест поиска без результатов"""
    test_data = [
        {'description': 'Ашан', 'category': 'Продукты'},
    ]

    result = simple_search('Пятерочка', test_data)
    assert len(result) == 0


def test_simple_search_empty_data():
    """Тест поиска с пустыми данными"""
    result = simple_search('test', [])
    assert result == []


def test_simple_search_none_data():
    """Тест поиска с None данными"""
    result = simple_search('test', None)
    assert result == []


def test_simple_search_error_handling():
    """Тест обработки ошибок в simple_search"""
    # Передаем некорректные данные
    result = simple_search('test', 'invalid_data')
    assert result == []
