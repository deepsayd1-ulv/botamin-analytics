from dataclasses import dataclass

@dataclass(frozen=True)
class DataConfig:
    FILE_PATH: str = "data/calls_week_anon.xlsx"
    
    # Исходные имена колонок из Excel
    COL_DATETIME: str = "дата и время"
    COL_DURATION: str = "длительность мин:сек"
    COL_TERMINATION: str = "причина завершения"
    COL_DIALOG: str = "история диалога юзер-бот"
    
    # Целевые имена колонок после предобработки
    TARGET_DATETIME: str = "call_datetime"
    TARGET_DURATION_SEC: str = "duration_seconds"