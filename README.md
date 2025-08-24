# 🏦 Анализатор банковских транзакций

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-orange?logo=pandas)](https://pandas.pydata.org/)
[![Pytest](https://img.shields.io/badge/Pytest-Testing%20Suite-green?logo=pytest)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

**Мощный и гибкий инструмент для анализа персональных финансов**, превращающий сырую выгрузку операций из Тинькофф-банка в наглядные отчеты, стратегические insights и автоматизированные расчеты.

---

## 🚀 5 КРУТЫХ ФИШЕК

1.  [**📊 Умная детализация трат по картам и категориям**](#-умная-детализация-трат-по-картам-и-категориям)
2.  [**🤖 Автоматическая генерация отчетов**](#-автоматическая-генерация-отчетов)
3.  [**📈 Интеграция с финансовыми API**](#-интеграция-с-финансовыми-api)
4.  [**🎯 Гибкий поиск и сервисы**](#-гибкий-поиск-и-сервисы)
5.  [**🧪 Всестороннее тестирование**](#-всестороннее-тестирование)

---

## 📊 Умная детализация трат по картам и категориям

Автоматическая группировка операций по картам, расчет кешбэка и выявление самых крупных транзакций.

**Пример использования:**
```bash
# Запуск основного отчета (использует текущую дату)
python -m src.main data/operations.csv
```

```bash
# Запуск отчета для конкретной даты
python -m src.main data/operations.csv --date 2024-03-01
```

**Пример вывода:**
```json
{
  "greeting": "Добрый вечер",
  "cards": [
    {
      "last_digits": "****5678",
      "total_spent": 15430.50,
      "cashback": 154.31
    }
  ],
  "top_transactions": [
    {
      "date": "2024-03-15",
      "amount": -12000.0,
      "category": "electronics",
      "description": "Ноутбук"
    }
  ]
}
```

---

## 🤖 Автоматическая генерация отчетов

Декоратор `@report_to_file` автоматически загружает данные и сохраняет отчеты в CSV/Excel.

**Пример использования:**
```python
from src.reports import spending_by_category, spending_by_weekday

# Автоматически сохранится в файл 'weekly_spending.csv'
df = spending_by_weekday('data/operations.csv', skip_save=False)

# Сохранится в указанный файл Excel
df = spending_by_category(
    'data/operations.csv', 
    category='Супермаркеты', 
    filename='supermarket_report.xlsx'
)
```

**Содержание generated `weekly_spending.csv`:**
```csv
День_недели,Средний_расход
Monday,1250.50
Tuesday,980.30
Wednesday,1540.20
...
```

---

## 📈 Интеграция с финансовыми API

Автоматическое получение актуальных курсов валют и котировок акций.

**Настройка API:**
```bash
# 1. Скопируйте .env.example в .env
# 2. Добавьте ваш API-ключ от Alpha Vantage
CURRENCY_API_KEY=your_actual_api_key_here
STOCK_API_KEY=your_actual_api_key_here
```

**Пример ответа API:**
```json
{
  "currency_rates": [
    {"currency": "USD", "rate": 75.50},
    {"currency": "EUR", "rate": 85.20}
  ],
  "stock_prices": [
    {"stock": "AAPL", "price": 150.12},
    {"stock": "TSLA", "price": 210.75}
  ]
}
```

---

## 🎯 Гибкий поиск и сервисы

Дополнительные сервисы для углубленного анализа финансов.

**Пример использования сервисов:**
```python
from src.services import analyze_cashback_categories, simple_search

# Анализ выгодных категорий для кешбэка 5%
cashback_analysis = analyze_cashback_categories(
    transactions_data, 
    year=2024, 
    month=3
)
# Результат: {'food': 125.0, 'transport': 85.50}

# Поиск транзакций по ключевым словам
search_results = simple_search(
    'Пятерочка', 
    transactions_data
)
# Найдет все операции с упоминанием "Пятерочка"
```

**Пример расчета инвестиционного копилка:**
```python
from src.services import investment_bank

# Расчет накоплений через округление трат до 100 рублей
savings = investment_bank(
    '2024-03', 
    transactions_data, 
    limit=100
)
# Результат: 243.0 (сумма округлений за месяц)
```

---

## 🧪 Всестороннее тестирование

Полное покрытие тестами обеспечивает надежность кода.

**Запуск тестов:**
```bash
# Все тесты
pytest tests/ -v

# Конкретный модуль
pytest tests/test_utils.py -v

# С покрытием кода
pytest --cov=src tests/
```

**Пример теста:**
```python
# tests/test_utils.py
def test_mask_card_number():
    """Тест маскировки номера карты"""
    assert mask_card_number('1234567812345678') == '****5678'
    assert mask_card_number('') == ""
    assert mask_card_number(None) == ""
```

---

## ⚙️ Установка и настройка

**1. Клонирование и установка:**
```bash
git clone <your-repo-url>
cd bank-transaction-analyser

python -m venv venv
source venv/bin/activate  # Linux/MacOS
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

**2. Подготовка данных:**
```bash
# Поместите вашу выгрузку из Тинькофф в папку data
cp ~/Downloads/operations.csv data/
```

**3. Запуск:**
```bash
# Основной отчет
python -m src.main data/operations.csv

# Справка по аргументам
python -m src.main --help
```

---

## 📁 Структура проекта

```
bank-transaction-analyser/
│
├── data/                 # Данные (выгрузки из банка)
│   ├── __init__.py
│   └── operations.csv    # Пример файла
│
├── src/                  # Исходный код
│   ├── __init__.py
│   ├── main.py          # Главный скрипт
│   ├── utils.py         # Утилиты (загрузка, фильтрация)
│   ├── reports.py       # Генерация отчетов
│   ├── views.py         # Представления для UI
│   └── services.py      # Дополнительные сервисы
│
├── tests/               # Тесты
│   ├── test_main.py
│   ├── test_utils.py
│   ├── test_reports.py
│   ├── test_services.py
│   └── test_views.py
│
├── flake8     # Набор конфигураций по коду
├── .env.template        # Пример env-файла
└── README.md           # Документация
```

---

## 🤝 Разработка

**Установка для разработки:**
```bash
pip install -r requirements.txt
pip install -e .  # Установка в режиме разработки
```

**Добавление нового отчета:**
```python
# 1. Добавьте функцию в src/reports.py
@report_to_file("my_report.csv")
def my_new_report(file_path, **kwargs):
    transactions = kwargs['transactions']
    # Ваша логика
    return result_df

# 2. Напишите тесты в tests/test_reports.py
def test_my_new_report():
    # Тестовая логика
    pass
```

---

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. Подробнее см. в файле MIT license.
