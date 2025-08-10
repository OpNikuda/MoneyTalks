from datetime import datetime
from typing import Dict, List
import pandas as pd
from src.utils import (
    filter_transactions_by_date,
    calculate_cashback,
    mask_card_number
)

def generate_home_data(df: pd.DataFrame, date_str: str) -> Dict:
    date = datetime.strptime(date_str, '%Y-%m-%d')
    start_date = date.replace(day=1)
    filtered_df = filter_transactions_by_date(df, start_date, date)

    # Обработка данных по картам
    cards = []
    for card in filtered_df['card_last_digits'].unique():
        card_df = filtered_df[filtered_df['card_last_digits'] == card]
        total_spent = card_df[card_df['amount'] < 0]['amount'].sum * - 1
        cards.append({
            'last_digits': mask_card_number(card),
            'total_spent': round(total_spent, 2),
            'cashback': round(calculate_cashback(total_spent), 2)
        })

    # Топ-5 транзакций
    top_trans = filtered_df.nlargest(5, 'amount')[['date', 'amount', 'category', 'description']]

    return {
        'cards': cards,
        'top_transactions': top_trans.to_dict('records'),
        'currency_rates': get_currency_rates(),  # Из views.py
        'stock_prices': get_stock_prices()       # Из views.py
    }

def get_currency_rates() -> List[Dict]:
    """Заглушка для курсов валют."""
    return [{'currency': 'USD', 'rate': 75.50}, {'currency': 'EUR', 'rate': 85.20}]

def get_stock_prices() -> List[Dict]:
    """Заглушка для акций."""
    return [{'stock': 'AAPL', 'price': 150.12}, {'stock': 'GOOGL', 'price': 2742.39}]