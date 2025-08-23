import pandas as pd
from datetime import datetime
from typing import Optional, Union, Any, Callable
import functools
import os
from pathlib import Path
from src.utils import load_transactions
import logging

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
            # 1. Загружаем данные
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

    Args:
        file_path: Путь к файлу с транзакциями
        category: Категория для анализа
        date: Дата отчета (опционально)
        **kwargs: Дополнительные аргументы

    Returns:
        DataFrame с тратами по месяцам для указанной категории
    """
    transactions = kwargs['transactions']
    logger.info(f"Генерация отчёта по категории '{category}'")

    # Проверяем наличие столбца category
    if 'category' not in transactions.columns:
        logger.warning("Столбец 'category' не найден в данных")
        return pd.DataFrame(columns=['Месяц', 'Категория', 'Сумма'])

    # Обработка даты
    date_obj = datetime.now() if date is None else pd.to_datetime(date)
    start_date = date_obj - pd.DateOffset(months=3)
    logger.debug(f"Период анализа: с {start_date.strftime('%Y-%m-%d')} по {date_obj.strftime('%Y-%m-%d')}")

    # Фильтрация данных
    mask = (
            (transactions['category'].str.lower() == category.lower()) &
            (transactions['amount'] < 0) &
            (transactions['date'] >= start_date) &
            (transactions['date'] <= date_obj)
    )
    filtered = transactions[mask].copy()

    if filtered.empty:
        logger.warning(f"Нет данных по категории '{category}' за указанный период")
        return pd.DataFrame(columns=['Месяц', 'Категория', 'Сумма'])

    logger.debug(f"Найдено {len(filtered)} транзакций по категории '{category}'")

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
    transactions = kwargs['transactions']
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
    transactions = kwargs['transactions']
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
