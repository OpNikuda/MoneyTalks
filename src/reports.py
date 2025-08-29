import functools
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pandas as pd

from src.utils import load_transactions

# Настройка логирования
logger = logging.getLogger(__name__)


# Декоратор для сохранения отчётов в файл
def report_to_file(default_filename: Optional[str] = None) -> Callable:
    """
    Декоратор для автоматического сохранения результатов функций в файл.
    Поддерживает CSV и Excel форматы.

    Args:
        default_filename: Имя файла по умолчанию для сохранения

    Returns:
        Декорированную функцию
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(file_path: Union[str, Path], *args: Any, **kwargs: Any) -> Any:
            # Проверяем, передан ли уже готовый DataFrame
            if 'transactions' in kwargs and isinstance(kwargs['transactions'], pd.DataFrame):
                transactions = kwargs['transactions']
                logger.debug(f"Используется переданный DataFrame размером {len(transactions)} строк")
            else:
                # 1. Загружаем данные из файла
                try:
                    logger.info(f"Загрузка данных из файла: {file_path}")
                    transactions = load_transactions(file_path)
                    kwargs['transactions'] = transactions
                    logger.debug(f"Успешно загружено {len(transactions)} транзакций")
                except Exception as e:
                    logger.error(f"Ошибка загрузки файла {file_path}: {str(e)}", exc_info=True)
                    raise

            # 2. Вызываем исходную функцию
            logger.debug(f"Вызов функции {func.__name__} с параметрами: {args}, {kwargs}")
            result = func(file_path, *args, **kwargs)

            # 3. Сохраняем результат только если не в тестовом режиме
            if not kwargs.get('skip_save', False):
                filename = kwargs.pop('filename', default_filename)
                if filename is None:
                    filename = (
                        f"report_{func.__name__}_"
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )

                try:
                    if isinstance(result, pd.DataFrame):
                        # Сохраняем в формате в зависимости от расширения
                        if filename.endswith(('.xls', '.xlsx')):
                            save_to_excel(result, filename, func.__name__)
                        else:
                            result.to_csv(filename, index=False)
                            logger.info(f"Отчёт сохранён в CSV: {os.path.abspath(filename)}. "
                                        f"Размер: {len(result)} строк")
                    else:
                        # Для не-DataFrame сохраняем как текст
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(str(result))
                        logger.info(f"Текстовый отчёт сохранён: {os.path.abspath(filename)}")
                except Exception as e:
                    logger.error(f"Ошибка сохранения отчёта {filename}: {str(e)}", exc_info=True)
                    raise

            logger.debug(f"Функция {func.__name__} завершена успешно")
            return result

        return wrapper

    # Обработка вызова без скобок (@report_to_file)
    if callable(default_filename):
        func = default_filename
        default_filename = None
        return decorator(func)

    return decorator


def save_to_excel(df: pd.DataFrame, filename: str, sheet_name: str) -> None:
    """
    Сохраняет DataFrame в Excel файл.

    Args:
        df: DataFrame для сохранения
        filename: Имя файла
        sheet_name: Имя листа
    """
    try:
        df.to_excel(filename, sheet_name=sheet_name[:31], index=False)  # Ограничение длины имени листа
        logger.info(f"Отчёт сохранён в Excel: {os.path.abspath(filename)}. "
                    f"Размер: {len(df)} строк")
    except Exception as e:
        logger.error(f"Ошибка сохранения в Excel {filename}: {str(e)}", exc_info=True)
        raise


# Отчёт: Траты по категории
@report_to_file()
def spending_by_category(
        file_path: Union[str, Path],
        category: str,
        date: Optional[str] = None,
        **kwargs: Any
) -> pd.DataFrame:
    """
    Генерирует отчет о тратах по указанной категории за последние 3 месяца.
    Может принимать как DataFrame, так и путь к файлу (CSV/XLSX).

    Args:
        file_path: Путь к файлу с транзакциями или DataFrame
        category: Категория для анализа
        date: Дата отчета (опционально)
        **kwargs: Дополнительные аргументы

    Returns:
        DataFrame с отчетом по тратам по категории
    """
    # Получаем транзакции из kwargs или загружаем из файла
    if 'transactions' in kwargs:
        df = kwargs['transactions']
        logger.debug("Используется переданный DataFrame")
    else:
        df = load_transactions(file_path)
        logger.debug(f"Загружен DataFrame из файла: {len(df)} строк")

    if 'category' not in df.columns:
        logger.warning("Столбец 'category' отсутствует в данных")
        return pd.DataFrame(columns=['Месяц', 'Категория', 'Сумма'])

    date_obj = datetime.now() if date is None else pd.to_datetime(date)
    start_date = date_obj - pd.DateOffset(months=3)

    logger.debug(f"Анализ категории '{category}' за период с {start_date} по {date_obj}")

    mask = (
            (df['category'].str.lower() == category.lower()) &
            (df['amount'] < 0) &
            (df['date'] >= start_date) &
            (df['date'] <= date_obj)
    )
    filtered = df[mask].copy()

    if filtered.empty:
        logger.info(f"Нет данных по категории '{category}' за указанный период")
        return pd.DataFrame(columns=['Месяц', 'Категория', 'Сумма'])

    result = (
        filtered
        .assign(Месяц=filtered['date'].dt.to_period('M'))
        .groupby(['Месяц', 'category'], as_index=False)
        .agg(Сумма=('amount', 'sum'))
        .rename(columns={'category': 'Категория'})
    )
    result['Сумма'] = result['Сумма'].abs()

    logger.info(f"Отчёт по категории '{category}' сгенерирован: {len(result)} записей")
    return result


# Отчёт: Траты по дням недели
@report_to_file("weekly_spending.csv")
def spending_by_weekday(
        file_path: Union[str, Path],
        date: Optional[str] = None,
        **kwargs: Any
) -> pd.DataFrame:
    """
    Анализирует средние траты по дням недели за последние 3 месяца.

    Args:
        file_path: Путь к файлу с транзакциями
        date: Дата отчета (опционально)
        **kwargs: Дополнительные аргументы

    Returns:
        DataFrame со средними тратами по дням недели
    """
    # Получаем транзакции из kwargs или загружаем из файла
    if 'transactions' in kwargs:
        transactions = kwargs['transactions']
        logger.debug("Используется переданный DataFrame для spending_by_weekday")
    else:
        transactions = load_transactions(file_path)
        logger.debug(f"Загружен DataFrame из файла для spending_by_weekday: {len(transactions)} строк")

    logger.info("Генерация отчёта по дням недели")

    date_obj = datetime.now() if date is None else pd.to_datetime(date)
    start_date = date_obj - pd.DateOffset(months=3)
    logger.debug(f"Период анализа: с {start_date.strftime('%Y-%m-%d')} по {date_obj.strftime('%Y-%m-%d')}")

    # Фильтрация трат
    mask = (
            (transactions['amount'] < 0) &
            (transactions['date'] >= start_date) &
            (transactions['date'] <= date_obj)
    )
    filtered = transactions[mask].copy()

    if filtered.empty:
        logger.warning("Нет данных о тратах за указанный период")
        return pd.DataFrame(columns=['День_недели', 'Средний_расход'])

    logger.debug(f"Найдено {len(filtered)} трат за период")

    # Добавляем день недели
    filtered['День_недели'] = filtered['date'].dt.day_name()

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
    logger.info(f"Отчёт по дням недели сгенерирован: {len(result)} записей")

    return result


# Отчёт: Траты в рабочие/выходные дни
@report_to_file()
def spending_by_workday(
        file_path: Union[str, Path],
        date: Optional[str] = None,
        **kwargs: Any
) -> pd.DataFrame:
    """
    Сравнивает траты в рабочие и выходные дни за последние 3 месяца.

    Args:
        file_path: Путь к файлу с транзакциями
        date: Дата отчета (опционально)
        **kwargs: Дополнительные аргументы

    Returns:
        DataFrame со средними тратами по типам дней
    """
    # Получаем транзакции из kwargs или загружаем из файла
    if 'transactions' in kwargs:
        transactions = kwargs['transactions']
        logger.debug("Используется переданный DataFrame для spending_by_workday")
    else:
        transactions = load_transactions(file_path)
        logger.debug(f"Загружен DataFrame из файла для spending_by_workday: {len(transactions)} строк")

    logger.info("Генерация отчёта по типам дней (рабочие/выходные)")

    date_obj = datetime.now() if date is None else pd.to_datetime(date)
    start_date = date_obj - pd.DateOffset(months=3)
    logger.debug(f"Период анализа: с {start_date.strftime('%Y-%m-%d')} по {date_obj.strftime('%Y-%m-%d')}")

    mask = (
            (transactions['amount'] < 0) &
            (transactions['date'] >= start_date) &
            (transactions['date'] <= date_obj)
    )
    filtered = transactions[mask].copy()

    if filtered.empty:
        logger.warning("Нет данных о тратах за указанный период")
        return pd.DataFrame(columns=['Тип_дня', 'Средний_расход'])

    logger.debug(f"Найдено {len(filtered)} трат за период")

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
    logger.info(f"Отчёт по типам дней сгенерирован: {len(result)} записей")

    return result