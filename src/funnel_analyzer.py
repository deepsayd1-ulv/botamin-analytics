import pandas as pd
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

def determine_funnel_step(dialog_text: str) -> int:
    """
    Определяет максимальный пройденный шаг воронки по тексту диалога.
    
    Шаги воронки:
    0 - Диалога нет или бот не начал разговор
    1 - Бот поздоровался и запросил согласие (начал разговор)
    2 - Клиент дал согласие, бот начал рассказывать про оффер
    3 - Договоренность о встрече/демо
    4 - Квалификация клиента (бюджет, ЛПР, сроки)
    
    Args:
        dialog_text: Текст диалога из колонки 'история диалога юзер-бот'
        
    Returns:
        int: Номер пройденного шага (0-4)
    """
    if pd.isna(dialog_text) or not dialog_text.strip():
        return 0
    
    dialog_lower = dialog_text.lower()
    
    # Шаг 1: Бот начал разговор (приветствие + запрос согласия)
    step1_markers = [
        "добрый день",
        "звоню насчёт",
        "тридцать секунд займет",
        "ладно?",
        "вам сейчас удобно говорить"
    ]
    
    has_step1_start = any(marker in dialog_lower for marker in step1_markers)
    
    if not has_step1_start:
        return 0
    
    # Проверяем, есть ли ответ клиента (значит, шаг 1 пройден)
    # Ищем паттерн "user:" в диалоге
    user_responses = re.findall(r'user:\s*([^\n]+)', dialog_text, re.IGNORECASE)
    
    if not user_responses:
        # Бот только начал, клиент не ответил
        return 1
    
    # Шаг 2: Клиент дал согласие, бот рассказывает про оффер
    # Ищем положительные ответы клиента
    positive_responses = ["да", "ага", "хорошо", "давай", "конечно", "слушаю", "рассказывай", "удобно"]
    has_consent = any(
        any(positive in response.lower() for positive in positive_responses)
        for response in user_responses
    )
    
    if not has_consent:
        # Клиент ответил, но отказал или задал вопрос
        return 1
    
    # Если есть согласие, проверяем, перешел ли бот к офферу
    # Ищем второе сообщение бота (после согласия клиента)
    bot_messages = re.findall(r'bot:\s*([^\n]+)', dialog_text, re.IGNORECASE)
    
    if len(bot_messages) < 2:
        # Бот только поздоровался, но не перешел к офферу
        return 1
    
    # Шаг 2: Бот рассказывает про оффер/преимущества
    step2_markers = [
        "оффер",
        "предложение",
        "условия",
        "стоимость",
        "цена",
        "скидка",
        "выгода",
        "кейс",
        "пример",
        "результат"
    ]
    
    has_step2 = any(
        any(marker in msg.lower() for marker in step2_markers)
        for msg in bot_messages[1:]  # Пропускаем первое приветствие
    )
    
    if not has_step2:
        return 1
    
    # Шаг 3: Договоренность о встрече
    step3_markers = [
        "встреча",
        "демо",
        "созвон",
        "созвониться",
        "показать",
        "рассказать подробнее",
        "в какое время",
        "когда удобно",
        "завтра",
        "послезавтра"
    ]
    
    has_step3 = any(
        any(marker in msg.lower() for marker in step3_markers)
        for msg in bot_messages
    )
    
    # Проверяем, согласился ли клиент на встречу
    meeting_consent = any(
        any(time_word in response.lower() for time_word in ["завтра", "послезавтра", "в 10", "в 11", "в 12", "в 14", "в 15", "в 16", "подходит", "договорились"])
        for response in user_responses
    )
    
    if has_step3 and meeting_consent:
        # Шаг 4: Квалификация (бюджет, ЛПР, сроки)
        step4_markers = [
            "бюджет",
            "кто принимает решение",
            "лицо, принимающее решение",
            "лпр",
            "сроки",
            "когда планируете",
            "сколько готовы"
        ]
        
        has_step4 = any(
            any(marker in msg.lower() for marker in step4_markers)
            for msg in bot_messages
        )
        
        if has_step4:
            return 4
    
    return 3 if has_step3 else 2


def analyze_funnel(df: pd.DataFrame, dialog_column: str = "история диалога юзер-бот") -> pd.DataFrame:
    """
    Добавляет в датафрейм колонку с номером пройденного шага воронки.
    
    Args:
        df: Датафрейм с данными звонков
        dialog_column: Название колонки с текстом диалога
        
    Returns:
        pd.DataFrame: Датафрейм с добавленной колонкой 'funnel_step'
    """
    logger.info("Начало анализа воронки диалогов")
    
    df_result = df.copy()
    df_result['funnel_step'] = df_result[dialog_column].apply(determine_funnel_step)
    
    # Логируем распределение по шагам
    step_counts = df_result['funnel_step'].value_counts().sort_index()
    logger.info("Распределение звонков по шагам воронки:\n%s", step_counts.to_string())
    
    # Логируем процентное соотношение
    total_calls = len(df_result)
    step_percentages = (step_counts / total_calls * 100).round(2)
    logger.info("Процентное соотношение по шагам:\n%s", step_percentages.to_string())
    
    logger.info("Анализ воронки завершен успешно")
    return df_result