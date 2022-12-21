from typing import Any
from loguru import logger
from telebot import types
import handlers
import loader
import keybords


@loader.bot.message_handler(commands=['start'])
def start_message(message: Any) -> None:  # message - текст сообщения
    """Старт бота, создание кнопки /help
    :param message:"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('/help')
    loader.bot.send_message(message.chat.id, 'Бот поиска отелей запущен', reply_markup=markup)


@loader.bot.message_handler(commands=['hello-world'])
def hello_message(message: Any) -> None:
    """Приветствие бота при введении команды /hello-world
    :param message:"""

    loader.bot.send_message(message.chat.id, f"Здравствуйте, я бот поиска отелей,\n"
                                             f"меня зовут:  {loader.bot.get_me().username}")


@loader.bot.message_handler(commands=['help'])
def help_message(message: Any) -> None:  # message - текст сообщения
    """Список команд вызываемый командой /help
    :param message:"""

    loader.bot.send_message(message.chat.id, '\n/lowprice - самые дешёвые отели в городе\n'
                                             '\n/highprice - самые дорогие отели в городе\n'
                                             '\n/bestdeal - наиболее подходящие по цене '
                                             'и расположению от центра')
    loader.bot.send_message(message.chat.id, '/history - история поиска отелей')


@loader.bot.message_handler(commands=['history'])
def out_history(message: Any) -> None:
    """Вывод истории запрошенных отелей
    :param message:"""
    loader.user_history(message)


@loader.bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def enter_command(message: Any) -> None:
    """Записываем выбранную команду в словарь пользователя
    :param message:"""

    loader.data_dict(message.chat.id)[0]['command'] = message.text
    logger.info(f"Введена команда: {message.text}")
    enter_city(message)


def enter_city(message: Any) -> None:
    """Запрос города и переход к функции city
    :param message:"""

    loader.bot.send_message(message.chat.id, "Выберите город:")
    loader.bot.register_next_step_handler(message, city)


def city(message: Any) -> None:
    """Получаем название города и его окружение, ориентиры (landmark)
    :param message:"""

    logger.info(f"Введен город: {message.text}, id_user: {message.from_user.id}, id_chat: {message.chat.id}")
    """Записываем название города введенное пользователем в словарь"""
    loader.data_dict(message.chat.id)[0]['enter_city'] = message.text
    pars_cl = loader.pars_city(message, message.text)
    """Проверяем что город существует и получаем его ID его "caption", 
    записываем полученный список в словарь"""
    capt_lst = handlers.city_id(message)
    loader.data_dict(message.chat.id)[0]['lst_city'] = capt_lst
    """Обрабатываем исключение timeout"""
    if pars_cl == handlers.err_dict.get('tio'):
        loader.bot.send_message(message.chat.id, handlers.err_dict.get('tio'))
        enter_city(message)
        """Обрабатываем исключение ошибки названия города"""
    elif capt_lst == handlers.err_dict.get('err_city'):
        loader.bot.send_message(message.chat.id, handlers.err_dict.get('err_city'))
        logger.error(f"Город: {message.text} не найден")
        enter_city(message)
    else:
        """Обработка полученных ID через InLineKeyboard и получение количества отелей"""
        loader.city_btn(message)
        loader.bot.register_next_step_handler(message, numm_hotels)


def numm_hotels_msg(message: Any) -> None:
    """Запрашиваем кол-во отелей и переходим к numm_hotels
    :param message:"""

    loader.bot.send_message(message.chat.id,
                            'Выберите количество отелей для просмотра\n(не более 8 шт.):')
    loader.bot.register_next_step_handler(message, numm_hotels)


def numm_hotels(message: Any) -> None:
    """Ввод количества отелей и обработка исключений
    :param message:"""

    numm = message.text
    logger.debug(f"Введено количество отелей: {numm}")
    """Обработка "re" введенного значения"""
    re_numm = handlers.numm_one(numm)
    if re_numm == handlers.err_dict.get('err_numm'):
        loader.bot.send_message(message.chat.id, handlers.err_dict.get('err_numm'))
        numm_hotels_msg(message)
    else:
        """Записываем количество отелей (после обработки re) в словарь"""
        loader.data_dict(message.chat.id)[0]['numm_hotels'] = re_numm + 1
        loader.bot.send_message(message.chat.id, f'Выбрано отелей:  {re_numm} шт.')
        check_in_date(message)


def check_in_date(message: Any) -> None:
    """ Создаем календарь и выбираем дату въезда в отель
    :param message:"""

    keybords.check_other_messages(message, keybords.calendar_1_callback, text='Выберите дату въезда:')

    @loader.bot.callback_query_handler(
        func=lambda call: call.data.startswith(keybords.calendar_1_callback.prefix)
    )
    def btn_inline(call: loader.CallbackQuery) -> None:
        """Обрабатываем callback нажатия кнопки и пишем в словарь
        :param call:"""

        z = keybords.call_btn(call, names_calendar=keybords.calendar_1_callback, text='Дата въезда:')
        loader.data_dict(call.message.chat.id)[0]['ch_in'] = z
        """Пока не выбрана дата дальше не идем"""
        if z is not None:
            logger.info(f"Дата въезда: {z}, id_user: {call.message.from_user.id}, id_chat: {call.message.chat.id}")
            check_out_date(call.message)


def check_out_date(message: Any) -> None:
    """Создаем календарь и выбираем дату выезда из отеля
    :param message:"""

    keybords.check_other_messages(message, keybords.calendar_2_callback, text='Выберите дату выезда:')

    @loader.bot.callback_query_handler(
        func=lambda call: call.data.startswith(keybords.calendar_2_callback.prefix)
    )
    def btn_inline(call: loader.CallbackQuery) -> None:
        """Обрабатываем callback нажатия кнопки и пишем в словарь
        :param call:"""

        z = keybords.call_btn(call, names_calendar=keybords.calendar_2_callback, text='Дата выезда:')
        """Пока не выбрана дата дальше не идем"""
        if z is not None:
            logger.info(f"Дата выезда: {z}, id_user: {call.message.from_user.id}, id_chat: {call.message.chat.id}")
            loader.data_dict(call.message.chat.id)[0]['ch_out'] = z
            """Проверка валидности даты (выезд не может быть ранее въезда)"""
            if handlers.check_date(loader.data_dict(call.message.chat.id)[0].get('ch_in'),
                                   loader.data_dict(call.message.chat.id)[0].get('ch_out')) == 'err':
                loader.bot.send_message(call.message.chat.id, handlers.err_dict.get('err_date'))
                check_in_date(call.message)
            else:
                loader.select_command(call.message)


@loader.bot.message_handler(content_types=['text'])
def hello_txt(message: Any) -> None:
    """Ответ бота на введенное сообщение - Привет (не зависит от регистра ввода)
    при вводе другого текста выдаст сообщение, что команда не существует
    :param message:"""

    if message.text.lower().strip() == 'привет':
        loader.bot.send_message(message.chat.id, 'Привет, готов помочь !\n'
                                                 'для вывода команд нажмите: /help')
    else:
        loader.bot.send_message(message.chat.id, 'Введенная команда не существует,\n'
                                                 'для справки нажмите /help')


if __name__ == '__main__':
    """Зацикливаем обработку команд бота с timeout=25"""
    loader.bot.infinity_polling(timeout=25)
