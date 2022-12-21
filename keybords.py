from typing import Any, List
import datetime
from loguru import logger
from telebot import types
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
import loader

"""Создаем календарь и 2 переменные для callback_query_handler"""
calendar = Calendar(language=RUSSIAN_LANGUAGE)
calendar_1_callback = CallbackData("calendar_1", "action", "year", "month", "day")
calendar_2_callback = CallbackData("calendar_2", "action", "year", "month", "day")


def check_other_messages(message, names_calendar, text) -> None:  # Здесь добавил переменные names, text
    """
    Catches a message with the command "start" and sends the calendar
    :param text: message - Выберите дату въезда:(выезда)
    :param names_calendar:  calendar_1_callback or calendar_2_callback
    :param message: chat
    :return:
    """

    now = datetime.datetime.now()  # Получить текущую дату
    loader.bot.send_message(
        message.chat.id,
        f"{text}",
        reply_markup=calendar.create_calendar(
            name=names_calendar.prefix,
            year=now.year,
            month=now.month,
        ),
    )


def call_btn(call, names_calendar, text) -> str or None:  # Здесь добавил переменные names, text
    """
    Обработка inline callback запросов
    :param text: message - Дата въезда: (выезда)
    :param names_calendar: calendar_1_callback or calendar_2_callback
    :param call: CallbackQuery
    :return:
    """
    """At this point, we are sure that this calendar is ours. So we cut the line by the separator of our calendar"""
    name, action, year, month, day = call.data.split(names_calendar.sep)
    # Processing the calendar. Get either the date or None if the buttons are of a different type
    date = calendar.calendar_query_handler(
        bot=loader.bot, call=call, name=name, action=action, year=year, month=month, day=day
    )
    """There are additional steps. Let's say if the date DAY is selected, you can execute your code. 
    I sent a message"""
    if action == "DAY":
        loader.bot.send_message(
            chat_id=call.from_user.id,
            text=f"{text}   {date.strftime('%Y-%m-%d')}",
            reply_markup='',
        )
        return date.strftime('%Y-%m-%d')
    elif action == "CANCEL":
        loader.bot.send_message(
            chat_id=call.from_user.id,
            text="Отмена выбора даты",
            reply_markup=''
        )
        """Возвращаем каку-то дату для CANCEL"""
        return '2015-01-01'
    else:
        return None


def create_landmark_btn(message: Any, btn_data: List) -> None:
    """Создаем клавиатуру и кнопки по списку
    :param message:
    :param btn_data: - список 'landmark' для клавиатуры"""

    markup = types.InlineKeyboardMarkup()
    for i_btn in range(len(btn_data)):
        markup.add(types.InlineKeyboardButton(text=btn_data[i_btn][1], callback_data=btn_data[i_btn][0]))
    loader.bot.send_message(message.chat.id, text="Уточните ориентир:", reply_markup=markup)
    logger.info(f"Список объектов по городу: {btn_data}"
                f"id_user {message.from_user.id}, id_chat: {message.chat.id}")


def create_photo_btn(message, id_hotel: int) -> None:
    """Создаем кнопки для выбора фото отеля"""

    markup = types.InlineKeyboardMarkup()
    btn_1 = types.InlineKeyboardButton(text='Да', callback_data=id_hotel)
    btn_2 = types.InlineKeyboardButton(text='Нет', callback_data=101)
    markup.add(btn_1, btn_2)
    loader.bot.send_message(message.chat.id, text="Загрузить фото отеля?", reply_markup=markup)
