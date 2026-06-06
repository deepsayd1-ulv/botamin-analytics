import logging
from src.data_loader import load_and_preprocess_data
from src.config import DataConfig
from src.funnel_analyzer import analyze_funnel
from src.metrics_calculator import calculate_funnel_metrics, calculate_additional_metrics, print_funnel_summary
from src.temporal_analyzer import analyze_temporal_patterns, print_temporal_summary
# Настройка логирования для всего приложения
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main() -> None:
    logger.info("Запуск пайплайна анализа данных Botamin")
    
    cfg = DataConfig()
    df = load_and_preprocess_data(cfg.FILE_PATH)
    
    if df is not None:
        logger.info("Предобработка завершена. Итоговые колонки: %s", list(df.columns))
        logger.info("Статистика по длительности (сек):\n%s", df['duration_seconds'].describe())
        
        # Шаг 2: Анализ воронки
        df_with_funnel = analyze_funnel(df, cfg.COL_DIALOG)
        
        # Шаг 3: Расчёт метрик
        df_metrics = calculate_funnel_metrics(df_with_funnel)
        additional_metrics = calculate_additional_metrics(df_with_funnel)
        
        # Выводим сводку
        print_funnel_summary(df_with_funnel)
        
        # Выводим пример для отладки
        logger.info("Пример диалогов с определенными шагами:")
        sample = df_with_funnel[[cfg.COL_DIALOG, 'funnel_step']].head(10)
        print(sample.to_string())
    else:
        logger.error("Не удалось загрузить данные. Работа прервана.")

if __name__ == "__main__":
    main()