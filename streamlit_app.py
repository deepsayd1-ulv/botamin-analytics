import streamlit as st
import pandas as pd
import logging
import requests          
import io

from src.data_loader import load_and_preprocess_data
from src.config import DataConfig
from src.funnel_analyzer import analyze_funnel
from src.dashboard import (
    create_funnel_chart,
    create_daily_trend_chart,
    create_termination_chart,
    create_duration_distribution_chart,
    calculate_kpi_metrics
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@st.cache_data(show_spinner="Загрузка и обработка данных...")
def load_data() -> pd.DataFrame:
    """Загружает и кэширует данные для дашборда."""
    cfg = DataConfig()
    
    # Пробуем загрузить локально (для разработки)
    try:
        df = load_and_preprocess_data(cfg.FILE_PATH)
        if df is not None:
            return analyze_funnel(df, cfg.COL_DIALOG)
    except Exception as e:
        logger.warning(f"Не удалось загрузить локально: {e}")
    
    # Для деплоя — загрузка по URL из GitHub
    try:
        url = "https://raw.githubusercontent.com/deepsayd1-ulv/botamin-analytics/main/data/calls_week_anon.xlsx"
        response = requests.get(url)
        response.raise_for_status()
        
        # Сохраняем временно
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        # Загружаем
        df = load_and_preprocess_data(tmp_path)
        
        # Удаляем временный файл
        os.unlink(tmp_path)
        
        if df is not None:
            return analyze_funnel(df, cfg.COL_DIALOG)
        else:
            st.error("Не удалось обработать данные")
            st.stop()
            
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        st.stop()
    
    df_with_funnel = analyze_funnel(df, cfg.COL_DIALOG)
    return df_with_funnel


def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Отрисовывает боковую панель с фильтрами и возвращает отфильтрованный датафрейм.
    """
    st.sidebar.title("🔍 Фильтры")
    
    # Фильтр по дате
    min_date = df['call_datetime'].min().date()
    max_date = df['call_datetime'].max().date()
    
    date_range = st.sidebar.date_input(
        "📅 Период",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Фильтр по длительности
    min_dur = float(df['duration_seconds'].min())
    max_dur = float(df['duration_seconds'].max())
    
    duration_range = st.sidebar.slider(
        "⏱️ Длительность звонка (сек)",
        min_value=min_dur,
        max_value=max_dur,
        value=(min_dur, max_dur),
        step=1.0
    )
    
    # Фильтр по причине завершения
    termination_options = ['Все'] + sorted(df['причина завершения'].unique().tolist())
    selected_termination = st.sidebar.selectbox(
        "📞 Причина завершения",
        options=termination_options
    )
    
    # Фильтр по шагу воронки
    step_options = ['Все'] + [f"Шаг {i}" for i in range(5)]
    selected_step = st.sidebar.selectbox(
        "🎯 Шаг воронки",
        options=step_options
    )
    
    # Применение фильтров
    filtered_df = df.copy()
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['call_datetime'].dt.date >= start_date) &
            (filtered_df['call_datetime'].dt.date <= end_date)
        ]
    
    filtered_df = filtered_df[
        (filtered_df['duration_seconds'] >= duration_range[0]) &
        (filtered_df['duration_seconds'] <= duration_range[1])
    ]
    
    if selected_termination != 'Все':
        filtered_df = filtered_df[filtered_df['причина завершения'] == selected_termination]
    
    if selected_step != 'Все':
        step_num = int(selected_step.split()[1])
        filtered_df = filtered_df[filtered_df['funnel_step'] == step_num]
    
    return filtered_df


def render_kpi_cards(metrics: dict) -> None:
    """Отрисовывает KPI-карточки в верхней части дашборда."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📞 Всего звонков",
            value=f"{int(metrics['total_calls'])}"
        )
    
    with col2:
        st.metric(
            label="❌ Без диалога",
            value=f"{int(metrics['no_dialog_count'])}",
            delta=f"-{metrics['no_dialog_pct']:.1f}%",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="✅ Контакт установлен",
            value=f"{int(metrics['contact_made_count'])}",
            delta=f"{metrics['contact_made_pct']:.1f}%"
        )
    
    with col4:
        st.metric(
            label="⏱️ Средняя длительность",
            value=f"{metrics['avg_duration']:.1f} сек"
        )


def main() -> None:
    """Основная функция дашборда."""
    st.set_page_config(
        page_title="Botamin Analytics Dashboard",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Аналитика голосового бота Botamin")
    st.markdown("---")
    
    # Загрузка данных
    df = load_data()
    
    # Боковая панель с фильтрами
    filtered_df = render_sidebar(df)
    
    # Информация о примененных фильтрах
    st.info(f"📊 Отображается {len(filtered_df)} из {len(df)} звонков")
    
    if len(filtered_df) == 0:
        st.warning("Нет данных, соответствующих выбранным фильтрам.")
        st.stop()
    
    # KPI-карточки
    metrics = calculate_kpi_metrics(filtered_df)
    render_kpi_cards(metrics)
    
    st.markdown("---")
    
    # Первый ряд графиков: Воронка + Причины завершения
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_funnel_chart(filtered_df), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_termination_chart(filtered_df), use_container_width=True)
    
    # Второй ряд: Динамика по дням
    st.plotly_chart(create_daily_trend_chart(filtered_df), use_container_width=True)
    
    # Третий ряд: Распределение длительности
    st.plotly_chart(create_duration_distribution_chart(filtered_df), use_container_width=True)
    
    # Таблица с сырыми данными (сворачиваемая)
    with st.expander("📋 Показать исходные данные"):
        display_columns = [
            'call_datetime', 'duration_seconds', 'причина завершения',
            'funnel_step', 'история диалога юзер-бот'
        ]
        st.dataframe(
            filtered_df[display_columns].head(100),
            use_container_width=True
        )


if __name__ == "__main__":
    main()