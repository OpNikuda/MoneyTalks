import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Union
import functools
import os
from pathlib import Path
from src.utils import load_transactions  # Импортируем вашу функцию


# Декоратор для сохранения отчётов в файл
def report_to_file(default_filename=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(file_path: Union[str, Path], *args, **kwargs):
            # 1. Загружаем данные
            try:
                transactions = load_transactions(file_path)
                kwargs['transactions'] = transactions  # Добавляем в kwargs
            except Exception as e:
                print(f"Ошибка загрузки файла {file_path}: {str(e)}")
                raise

            # 2. Вызываем исходную функцию
            result = func(file_path, *args, **kwargs)

            # 3. Сохраняем результат
            filename = kwargs.pop('filename', default_filename)
            if filename is None:
                filename = (
                    f"report_{func.__name__}_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )

            try:
                if isinstance(result, pd.DataFrame):
                    result.to_csv(filename, index=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(str(result))
                print(f"Отчёт сохранён: {os.path.abspath(filename)}")
            except Exception as e:
                print(f"Ошибка сохранения отчёта: {str(e)}")
                raise

            return result

        return wrapper

    # Обработка вызова без скобок (@report_to_file)
    if callable(default_filename):
        func = default_filename
        default_filename = None
        return decorator(func)

    return decorator


# Отчёт: Траты по категории
@report_to_file()
def spending_by_category(
        file_path: Union[str, Path],
        category: str,
        date: Optional[str] = None,
        **kwargs
) -> pd.DataFrame:
    transactions = kwargs['transactions']

    # Проверяем наличие столбца category
    if 'category' not in transactions.columns:
        return pd.DataFrame(columns=['Месяц', 'Категория', 'Сумма'])

    # Обработка даты
    date_obj = datetime.now() if date is None else pd.to_datetime(date)
    start_date = date_obj - pd.DateOffset(months=3)

    # Фильтрация данных
    mask = (
            (transactions['category'].str.lower() == category.lower()) &
            (transactions['amount'] < 0) &
            (transactions['date'] >= start_date) &
            (transactions['date'] <= date_obj)
    )
    filtered = transactions[mask].copy()

    if filtered.empty:
        return pd.DataFrame(columns=['Месяц', 'Категория', 'Сумма'])

    # Агрегация по месяцам
    result = (
        filtered
        .assign(Месяц=filtered['date'].dt.to_period('M'))
        .groupby(['Месяц', 'category'], as_index=False)
        .agg(Сумма=('amount', 'sum'))
        .rename(columns={'category': 'Категория'})
    )

    # Делаем суммы положительными
    result['Сумма'] = result['Сумма'].abs()

    return result


# Отчёт: Траты по дням недели
@report_to_file("weekly_spending.csv")
def spending_by_weekday(
        file_path: Union[str, Path],
        date: Optional[str] = None,
        **kwargs
) -> pd.DataFrame:
    transactions = kwargs['transactions']

    date_obj = datetime.now() if date is None else pd.to_datetime(date)
    start_date = date_obj - pd.DateOffset(months=3)

    # Фильтрация трат
    mask = (
            (transactions['amount'] < 0) &
            (transactions['date'] >= start_date) &
            (transactions['date'] <= date_obj)
    )
    filtered = transactions[mask].copy()

    if filtered.empty:
        return pd.DataFrame(columns=['День_недели', 'Средний_расход'])

    # Добавляем день недели (понедельник=0)
    filtered['День_недели'] = (
        filtered['date'].dt.day_name()
    )

    # Группировка и сортировка
    weekdays_order = [
        'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]

    result = (
        filtered
        .groupby('День_недели', as_index=False)
        .agg(Средний_расход=('amount', 'mean'))
        .sort_values(
            'День_недели',
            key=lambda x: x.map({day: i for i, day in enumerate(weekdays_order)})
        )
    )

    # Округление и абсолютные значения
    result['Средний_расход'] = result['Средний_расход'].abs().round(2)

    return result


# Отчёт: Траты в рабочие/выходные дни
@report_to_file()
def spending_by_workday(
        file_path: Union[str, Path],
        date: Optional[str] = None,
        **kwargs
) -> pd.DataFrame:
    transactions = kwargs['transactions']

    date_obj = datetime.now() if date is None else pd.to_datetime(date)
    start_date = date_obj - pd.DateOffset(months=3)

    mask = (
            (transactions['amount'] < 0) &
            (transactions['date'] >= start_date) &
            (transactions['date'] <= date_obj)
    )
    filtered = transactions[mask].copy()

    if filtered.empty:
        return pd.DataFrame(columns=['Тип_дня', 'Средний_расход'])

    # Определяем тип дня
    filtered['Тип_дня'] = (
        filtered['date'].apply(
            lambda x: 'Выходной' if x.weekday() >= 5 else 'Рабочий'
        )
    )

    result = (
        filtered
        .groupby('Тип_дня', as_index=False)
        .agg(Средний_расход=('amount', 'mean'))
    )

    result['Средний_расход'] = result['Средний_расход'].abs().round(2)

    return result