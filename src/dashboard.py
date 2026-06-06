import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def create_funnel_chart(df: pd.DataFrame) -> go.Figure:
    """
    Строит график воронки: количество звонков на каждом шаге.
    
    Args:
        df: Датафрейм с колонкой 'funnel_step'
        
    Returns:
        go.Figure: График воронки
    """
    step_descriptions = {
        0: "Шаг 0: Нет диалога",
        1: "Шаг 1: Бот поздоровался",
        2: "Шаг 2: Согласие + оффер",
        3: "Шаг 3: Встреча",
        4: "Шаг 4: Квалификация"
    }
    
    step_counts = df['funnel_step'].value_counts().sort_index()
    
    # Гарантируем, что все шаги присутствуют
    data = []
    for step in range(5):
        count = int(step_counts.get(step, 0))
        data.append({
            'Шаг': step_descriptions[step],
            'Количество': count,
            'Шаг номер': step
        })
    
    df_funnel = pd.DataFrame(data)
    
    fig = go.Figure(go.Funnel(
        y=df_funnel['Шаг'].tolist(),
        x=df_funnel['Количество'].tolist(),
        textinfo="value+percent initial",
        marker=dict(
            color=[
                '#FF6B6B' if step == 0 else
                '#FFA500' if step == 1 else
                '#FFD700' if step == 2 else
                '#90EE90' if step == 3 else
                '#4CAF50'
                for step in df_funnel['Шаг номер']
            ]
        ),
        connector=dict(line=dict(color="royalblue", dash="dot", width=2))
    ))
    
    fig.update_layout(
        title="Воронка диалогов голосового бота",
        font=dict(size=14),
        height=500
    )
    
    return fig


def create_daily_trend_chart(df: pd.DataFrame) -> go.Figure:
    """
    Строит линейный график динамики звонков по дням с разбивкой по шагам.
    """
    df_copy = df.copy()
    df_copy['call_date'] = df_copy['call_datetime'].dt.date
    
    daily = df_copy.groupby(['call_date', 'funnel_step']).size().reset_index(name='count')
    daily_pivot = daily.pivot(index='call_date', columns='funnel_step', values='count').fillna(0)
    
    fig = go.Figure()
    
    step_colors = {0: '#FF6B6B', 1: '#FFA500', 2: '#FFD700', 3: '#90EE90', 4: '#4CAF50'}
    step_names = {
        0: "Нет диалога",
        1: "Бот поздоровался",
        2: "Согласие + оффер",
        3: "Встреча",
        4: "Квалификация"
    }
    
    for step in sorted(daily_pivot.columns):
        fig.add_trace(go.Scatter(
            x=daily_pivot.index,
            y=daily_pivot[step],
            mode='lines+markers',
            name=step_names.get(step, f"Шаг {step}"),
            line=dict(color=step_colors.get(step, '#808080'), width=2),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="Динамика звонков по дням и шагам воронки",
        xaxis_title="Дата",
        yaxis_title="Количество звонков",
        hovermode='x unified',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_termination_chart(df: pd.DataFrame) -> go.Figure:
    """
    Строит столбчатую диаграмму причин завершения звонков.
    """
    termination_counts = df['причина завершения'].value_counts().reset_index()
    termination_counts.columns = ['Причина', 'Количество']
    
    fig = px.bar(
        termination_counts,
        x='Причина',
        y='Количество',
        color='Причина',
        color_discrete_map={
            'bot_hangup': '#FF6B6B',
            'client_hangup': '#4ECDC4'
        },
        text='Количество'
    )
    
    fig.update_layout(
        title="Распределение причин завершения звонков",
        xaxis_title="Причина завершения",
        yaxis_title="Количество звонков",
        showlegend=False,
        height=400
    )
    
    fig.update_traces(textposition='outside')
    
    return fig


def create_duration_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Строит гистограмму распределения длительности звонков по шагам.
    """
    fig = px.histogram(
        df,
        x='duration_seconds',
        color='funnel_step',
        nbins=20,
        barmode='overlay',
        opacity=0.7,
        color_discrete_map={
            0: '#FF6B6B',
            1: '#FFA500',
            2: '#FFD700',
            3: '#90EE90',
            4: '#4CAF50'
        },
        labels={
            'duration_seconds': 'Длительность (сек)',
            'funnel_step': 'Шаг воронки'
        }
    )
    
    fig.update_layout(
        title="Распределение длительности звонков по шагам воронки",
        height=400
    )
    
    return fig


def calculate_kpi_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Рассчитывает ключевые показатели для отображения в KPI-карточках.
    """
    total_calls = len(df)
    no_dialog = len(df[df['funnel_step'] == 0])
    step1_plus = len(df[df['funnel_step'] >= 1])
    avg_duration = float(df['duration_seconds'].mean()) if total_calls > 0 else 0.0
    
    return {
        'total_calls': float(total_calls),
        'no_dialog_count': float(no_dialog),
        'no_dialog_pct': (no_dialog / total_calls * 100) if total_calls > 0 else 0.0,
        'contact_made_count': float(step1_plus),
        'contact_made_pct': (step1_plus / total_calls * 100) if total_calls > 0 else 0.0,
        'avg_duration': avg_duration
    }