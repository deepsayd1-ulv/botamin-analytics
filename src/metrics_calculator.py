import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def calculate_funnel_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Рассчитывает метрики воронки: абсолютные значения и конверсии между шагами.
    """
    logger.info("Начало расчёта метрик воронки")
    
    step_counts = df['funnel_step'].value_counts().sort_index()
    metrics_data = []
    total_calls = len(df)
    
    for step in range(5):
        count = step_counts.get(step, 0)
        percent_of_total = (count / total_calls * 100) if total_calls > 0 else 0
        
        if step == 0:
            conversion_from_prev = 100.0
        else:
            reached_current_or_higher = sum(step_counts.get(s, 0) for s in range(step, 5))
            reached_previous_or_higher = sum(step_counts.get(s, 0) for s in range(step - 1, 5))
            
            if reached_previous_or_higher > 0:
                conversion_from_prev = (reached_current_or_higher / reached_previous_or_higher * 100)
            else:
                conversion_from_prev = 0.0
        
        metrics_data.append({
            'Шаг воронки': step,
            'Описание': _get_step_description(step),
            'Количество звонков': int(count),
            '% от общего числа': round(percent_of_total, 2),
            'Конверсия с пред. шага, %': round(conversion_from_prev, 2)
        })
    
    df_metrics = pd.DataFrame(metrics_data)
    logger.info("Таблица метрик воронки:\n%s", df_metrics.to_string(index=False))
    return df_metrics


def _get_step_description(step: int) -> str:
    descriptions = {
        0: "Нет диалога (клиент сбросил сразу)",
        1: "Бот поздоровался (клиент не ответил)",
        2: "Клиент дал согласие (бот рассказывает оффер)",
        3: "Договорённость о встрече",
        4: "Квалификация клиента"
    }
    return descriptions.get(step, "Неизвестный шаг")


def calculate_additional_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Рассчитывает дополнительные метрики для анализа."""
    logger.info("Расчёт дополнительных метрик")
    
    metrics = {}
    
    no_dialog_calls = df[df['funnel_step'] == 0]
    metrics['Средняя длительность без диалога (сек)'] = (
        float(no_dialog_calls['duration_seconds'].mean()) if len(no_dialog_calls) > 0 else 0.0
    )
    
    with_dialog_calls = df[df['funnel_step'] >= 1]
    metrics['Средняя длительность с диалогом (сек)'] = (
        float(with_dialog_calls['duration_seconds'].mean()) if len(with_dialog_calls) > 0 else 0.0
    )
    
    metrics['% звонков без диалога'] = (
        float(len(no_dialog_calls) / len(df) * 100) if len(df) > 0 else 0.0
    )
    
    # Распределение причин завершения
    termination_counts = df['причина завершения'].value_counts()
    for reason, count in termination_counts.items():
        metrics[f'Причина завершения: {reason}'] = int(count)
    
    logger.info("Дополнительные метрики рассчитаны")
    return metrics


def print_funnel_summary(df: pd.DataFrame) -> None:
    """Выводит сводку по воронке в консоль."""
    print("\n" + "="*80)
    print("СВОДКА ПО ВОРОНКЕ БОТА")
    print("="*80)
    
    df_metrics = calculate_funnel_metrics(df)
    print("\nТаблица конверсий:")
    print(df_metrics.to_string(index=False))
    
    additional_metrics = calculate_additional_metrics(df)
    print("\nДополнительные метрики:")
    for key, value in additional_metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("="*80 + "\n")