import pandas as pd
import logging
from typing import Optional
from .config import DataConfig

logger = logging.getLogger(__name__)

def load_and_preprocess_data(file_path: str) -> Optional[pd.DataFrame]:
    """
    Загружает Excel-файл с данными звонков и выполняет первичную очистку.
    
    Args:
        file_path: Путь к файлу calls_week_anon.xlsx
        
    Returns:
        pd.DataFrame: Очищенный датафрейм или None в случае критической ошибки.
    """
    try:
        logger.info(f"Начало загрузки данных из {file_path}")
        
        # 1. Загрузка данных (используем openpyxl для .xlsx)
        df = pd.read_excel(file_path, engine='openpyxl')
        logger.info(f"Данные успешно загружены. Размер датафрейма: {df.shape}")
        
        # 2. Первичный анализ (выводим в лог для отладки)
        logger.debug("Первые 3 строки данных:\n%s", df.head(3).to_string())
        logger.debug("Информация о типах данных:\n%s", df.info(memory_usage='deep'))
        logger.debug("Количество пропусков (NaN) по колонкам:\n%s", df.isnull().sum().to_dict())
        
        cfg = DataConfig()
        
        # 3. Преобразование даты и времени
        if cfg.COL_DATETIME in df.columns:
            # Формат в примере: "5/29/26 18:00" -> месяц/день/год часы:минуты
            df[cfg.TARGET_DATETIME] = pd.to_datetime(
                df[cfg.COL_DATETIME], 
                format='%m/%d/%y %H:%M', 
                errors='coerce'
            )
            logger.info(f"Колонка '{cfg.COL_DATETIME}' преобразована в datetime.")
        else:
            logger.error(f"Колонка '{cfg.COL_DATETIME}' не найдена в файле.")
            return None

        # 4. Преобразование длительности из формата "м:сс" или "мм:сс" в секунды (float)
        if cfg.COL_DURATION in df.columns:
            # Разбиваем строку по двоеточию для надежного извлечения минут и секунд
            duration_split = df[cfg.COL_DURATION].astype(str).str.split(':', expand=True)
            
            # Приводим к числовому типу. errors='coerce' защитит от мусора в данных
            minutes = pd.to_numeric(duration_split[0], errors='coerce').fillna(0).astype(int)
            seconds = pd.to_numeric(duration_split[1], errors='coerce').fillna(0).astype(int)
            
            # Итоговая формула перевода в секунды
            df[cfg.TARGET_DURATION_SEC] = (minutes * 60 + seconds).astype(float)
            logger.info("Длительность звонка успешно преобразована в секунды.")
        else:
            logger.error(f"Колонка '{cfg.COL_DURATION}' не найдена в файле.")
            return None

        # 5. Очистка от невалидных дат
        initial_len = len(df)
        df = df.dropna(subset=[cfg.TARGET_DATETIME])
        dropped_len = initial_len - len(df)
        if dropped_len > 0:
            logger.warning(f"Удалено {dropped_len} строк из-за невалидной даты.")

        # 6. Приведение типов для категориальных данных (оптимизация памяти)
        if cfg.COL_TERMINATION in df.columns:
            df[cfg.COL_TERMINATION] = df[cfg.COL_TERMINATION].astype('category')
        
        if cfg.COL_DIALOG in df.columns:
            # Заполняем пропуски в диалогах пустой строкой для безопасной обработки текстом позже
            df[cfg.COL_DIALOG] = df[cfg.COL_DIALOG].fillna("").astype(str)

        logger.info("Первичная обработка данных завершена успешно.")
        return df

    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Критическая ошибка при обработке данных: {e}", exc_info=True)
        return None