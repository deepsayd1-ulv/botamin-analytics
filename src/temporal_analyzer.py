import pandas as pd
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def analyze_temporal_patterns(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Анализирует временные паттерны: динамика по дням, по времени суток, причины завершения по шагам.
    
    Args:
        df: Датафрейм с данными звонков и колонкой 'funnel_step'
        
    Returns:
        Dict: Словарь с датафреймами для различных временных срезов
    """
    logger.info("Начало анализа временных паттернов")
    
    results = {}
    
    # 1. Динамика по дням
    df['call_date'] = df['call_datetime'].dt.date
    daily_stats = df.groupby('call_date').agg({
        'funnel_step': [
            ('total_calls', 'count'),
            ('avg_step', 'mean'),
            ('step_0_count', lambda x: (x == 0).sum()),
            ('step_1_count', lambda x: (x == 1).sum()),
            ('step_2_plus_count', lambda x: (x >= 2).sum())
        ]
    })
    
    # Упрощаем структуру колонок
    daily_stats.columns = ['total_calls', 'avg_step', 'step_0_count', 'step_1_count', 'step_2_plus_count']
    daily_stats['conversion_to_step_1_pct'] = (
        (daily_stats['step_1_count'] + daily_stats['step_2_plus_count']) / daily_stats['total_calls'] * 100
    ).round(2)
    daily_stats = daily_stats.reset_index()
    
    results['daily_stats'] = daily_stats
    logger.info("Статистика по дням:\n%s", daily_stats.to_string(index=False))
    
    # 2. Динамика по часам (время суток)
    df['call_hour'] = df['call_datetime'].dt.hour
    hourly_stats = df.groupby('call_hour').agg({
        'funnel_step': [
            ('total_calls', 'count'),
            ('avg_step', 'mean'),
            ('step_0_count', lambda x: (x == 0).sum()),
            ('step_1_count', lambda x: (x == 1).sum())
        ]
    })
    
    hourly_stats.columns = ['total_calls', 'avg_step', 'step_0_count', 'step_1_count']
    hourly_stats['conversion_to_step_1_pct'] = (
        hourly_stats['step_1_count'] / hourly_stats['total_calls'] * 100
    ).round(2)
    hourly_stats = hourly_stats.reset_index()
    
    results['hourly_stats'] = hourly_stats
    logger.info("Статистика по часам:\n%s", hourly_stats.to_string(index=False))
    
    # 3. Распределение причин завершения по шагам
    termination_by_step = df.groupby(['funnel_step', 'причина завершения']).size().unstack(fill_value=0)
    termination_by_step = termination_by_step.reset_index()
    
    results['termination_by_step'] = termination_by_step
    logger.info("Причины завершения по шагам:\n%s", termination_by_step.to_string(index=False))
    
    # 4. Средняя длительность по шагам и причинам завершения
    duration_stats = df.groupby(['funnel_step', 'причина завершения'])['duration_seconds'].agg([
        ('mean_duration', 'mean'),
        ('median_duration', 'median'),
        ('count', 'count')
    ]).round(2)
    
    duration_stats = duration_stats.reset_index()
    results['duration_stats'] = duration_stats
    logger.info("Длительность по шагам и причинам:\n%s", duration_stats.to_string(index=False))
    
    logger.info("Анализ временных паттернов завершен")
    return results


def print_temporal_summary(temporal_results: Dict[str, pd.DataFrame]) -> None:
    """Выводит сводку по временным паттернам в консоль."""
    print("\n" + "="*80)
    print("АНАЛИЗ ВРЕМЕННЫХ ПАТТЕРНОВ")
    print("="*80)
    
    print("\n1. Динамика по дням:")
    print(temporal_results['daily_stats'].to_string(index=False))
    
    print("\n2. Динамика по часам:")
    print(temporal_results['hourly_stats'].to_string(index=False))
    
    print("\n3. Причины завершения по шагам:")
    print(temporal_results['termination_by_step'].to_string(index=False))
    
    print("\n4. Средняя длительность по шагам и причинам:")
    print(temporal_results['duration_stats'].to_string(index=False))
    
    print("="*80 + "\n")