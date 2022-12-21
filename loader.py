from typing import Any, Union, Dict, Tuple, List, Optional
from loguru import logger
from os import getenv
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import CallbackQuery
from datetime import datetime
from time import time
import re
import handlers
import rapidapi
import keybords
import history_data

load_dotenv()   # Подгружаем .env
key_bot = getenv('token')   # Выбираем ключ для telegram
key_hotel = getenv('x-rapidapi-key')    # Выбираем ключ rapid

"""Активируем бота"""
bot = TeleBot(token=key_bot)
logger.info(f"Телеграм-бот запущен")


class User:
    """Класс пользователя со словарем для хранения данных"""
    users = dict()

    def __init__(self, id_user: int = None) -> None:
        """
        __init__
        :param id_user: ID пользователя
        """

        self.id_user = id_user

    @classmethod
    def add_user(cls, id_user: int) -> Dict:
        """Добавляем нового пользователя
        :param id_user: - ID пользователя"""

        cls.users[id_user] = dict()
        return cls.users

    def get_user(self, id_user: int) -> Tuple:
        """Получаем существующего пользователя
        :param id_user: - ID пользователя"""

        if self.id_user not in self.users:
            User.add_user(id_user)
            res = self.users.get(self.id_user)
        else:
            res = self.users.get(self.id_user)
        return res, self.users


def data_dict(cur_id: int) -> Tuple:    # (dict, id_user:dict)
    """Добавляем пользователя через get_user (или читаем если такой есть)
    :param cur_id: - ID пользователя"""

    user_tlg = User(cur_id)
    data = user_tlg.get_user(cur_id)
    # print('data = ', data)
    return data


def pars_city(message: Any, name_city: str) -> str:
    """Вызываем класс HotelsApi, передаем параметр - навзвание города
    получаем данные в словарь с ключем city_search.json
    :param message:
    :param name_city: - название города"""

    data_city = rapidapi.HotelsApi(name_city)
    res = data_city.query_city(message)
    return res


def city_btn(message: Any) -> None:
    """InLine кнопки для уточнения выбора окружения города
    :param message:"""

    sel_city = data_dict(message.chat.id)[0].get('lst_city')
    keybords.create_landmark_btn(message, btn_data=sel_city)

    @bot.callback_query_handler(func=lambda call_city: call_city.data in str(sel_city))
    def query_handler(call_city: CallbackQuery) -> None:
        """Обработка callback кнопки и переход к вводу кол. отелей
        :param call_city: - callback_data (ID выбранного города)"""

        answer = ''
        for call_btn in range(len(sel_city)):
            if call_city.data == str(sel_city[call_btn][0]):
                answer = sel_city[call_btn][1]
        bot.send_message(call_city.message.chat.id, f'Выбран: {answer}')
        """Записываем ID выборки города и его название (answer) в словарь"""
        data_dict(call_city.message.chat.id)[0]['id_req_city'] = call_city.data
        data_dict(call_city.message.chat.id)[0]['req_city'] = answer
        bot.edit_message_reply_markup(call_city.message.chat.id, call_city.message.message_id)
        """Запрашиваем количество отелей для вывода и переходим main.numm_hotels"""
        bot.send_message(call_city.message.chat.id, 'Выберите количество отелей для просмотра\n(не более 8 шт.):')


def hotels_lst(message: Any) -> str:
    """Присваиваем переменным данные из словаря пользователя
        и формируем запросы lowprice, highprice и bestdeal
    :param message:"""

    data = data_dict(message.chat.id)[0]
    command = data.get('command')
    id_city = data.get('id_req_city')   # В словаре данные типа INT
    numm_hotels = data.get('numm_hotels')   # В словаре данные типа INT
    check_in = data.get('ch_in')
    check_out = data.get('ch_out')
    if command == '/lowprice':
        """Обработка команды lowprice"""
        z = rapidapi.HotelsApi.query_hotel(message, id_city=id_city, numm_hotels=numm_hotels,
                                           check_in=check_in, check_out=check_out)
        if z == handlers.err_dict.get('tio'):
            return 'tio_err'
    elif command == '/highprice':
        """Обработка команды highprice"""
        sort_order = data.get('sort_order')
        z = rapidapi.HotelsApi.query_hotel(message, id_city=id_city, numm_hotels=numm_hotels,
                                           check_in=check_in, check_out=check_out,
                                           sort_order=sort_order)
        if z == handlers.err_dict.get('tio'):
            return 'tio_err'
    elif command == '/bestdeal':
        """Обработка команды bestdeal"""
        sort_order = data.get('sort_order')
        min_price = int(data.get('min_price'))
        max_price = int(data.get('max_price'))
        z = rapidapi.HotelsApi.query_hotel(message, id_city=id_city, numm_hotels=25,
                                           check_in=check_in, check_out=check_out,
                                           min_price=min_price, max_price=max_price,
                                           sort_order=sort_order)
        if z == handlers.err_dict.get('tio'):
            return 'tio_err'


def load_hotel(message: Any) -> None:
    """Проверяем загружаемые данные, в случае ошибки завершаем запрос
    :param message:"""

    resp = hotels_lst(message)
    if resp == 'tio_err':
        bot.send_message(message.chat.id, handlers.err_dict.get('tio'))
        end(message)
    else:
        check_data = info_hotels(message)
        if check_data == 'err':
            """Если данные не обрабатываются, то завершаем обработку запроса"""
            bot.send_message(message.chat.id, f'Отели для вывода отсутствуют, '
                                              f'проверьте введенные данные и '
                                              f'повторите запрос')
            end(message)


def select_command(message: Any) -> None:
    """Определяем действия для комманд lowprice, highprice, bestdeal
    :param message:"""

    user_dict = data_dict(message.chat.id)[0]
    result = handlers.check_command(sel_command=user_dict)
    if result == 'low' or result == 'high':
        load_hotel(message)
    elif result == 'best':
        best_deal(message)


def best_deal(message: Any) -> None:
    """Принимаем ввод диапазона цен
    :param message:"""

    bot.send_message(message.chat.id, 'Введите через пробел диапазон цен в рублях:')
    bot.register_next_step_handler(message, best_deal_price)


def best_deal_price(message: Any) -> None:
    """Получаем диапазан цен, проверяем и пишем в словарь пользователя
    :param message:"""

    renumm = handlers.numm_range(message.text)
    if renumm == handlers.err_dict.get('err_range'):
        bot.send_message(message.chat.id, handlers.err_dict.get('err_range'))
        best_deal(message)
    else:
        data_dict(message.chat.id)[0]['min_price'] = renumm[0]  # int
        data_dict(message.chat.id)[0]['max_price'] = renumm[1]  # int
        bot.send_message(message.chat.id, 'Введите через пробел диапазон расстояния от центра:')
        bot.register_next_step_handler(message, best_deal_dist)


def best_deal_dist(message: Any) -> None:
    """Получаем диапазан расстояний от центра, проверяем и пишем в словарь пользователя
    :param message"""

    renumm = handlers.numm_range(message.text)
    if renumm == handlers.err_dict.get('err_range'):
        bot.send_message(message.chat.id, handlers.err_dict.get('err_range'))
        best_deal(message)
    else:
        data_dict(message.chat.id)[0]['min_dist'] = renumm[0]  # int
        data_dict(message.chat.id)[0]['max_dist'] = renumm[1]  # int
        load_hotel(message)


def idx_hotels(message: Any) -> Union[List, str]:
    """Формируем список индексов отелея для вывода
    :param message:"""

    min_dist = data_dict(message.chat.id)[0].get('min_dist')
    max_dist = data_dict(message.chat.id)[0].get('max_dist')

    if (min_dist and max_dist) is None:  # для lowprice / highprice
        """Условия для команд lowprice / highprice"""
        numms = (data_dict(message.chat.id)[0]['numm_hotels'] - 1)
        idx_lst = [i for i in range(numms)]

    else:
        """Условие для команды bestdeal"""
        idx_lst = handlers.idx_range(message, min_dist=min_dist, max_dist=max_dist)

        """Ограничиваем количество выводимых отелей"""
        if len(idx_lst) > 8:
            idx_lst = idx_lst[:8]

        """Ограничиваем список введенным количеством отелей"""
        numms = (data_dict(message.chat.id)[0]['numm_hotels'] - 1)
        idx_lst = idx_lst[:numms]

    try:
        idx_lst[0]
    except IndexError:
        logger.error(f"Нет данных для выбора")
        return 'err'
    logger.info(f"Диапазон индексов для вывода: {idx_lst}")
    return idx_lst


def info_hotels(message: Any) -> Optional[str]:
    """Получаем данные из словаря пользователя, ключ - hotels_search.json
    :param message:"""

    start_time = time()

    data_hotels = data_dict(message.chat.id)[0].get('hotels_search.json')
    idx_lst = idx_hotels(message)

    for i in idx_lst:
        res = handlers.hotel_dict(hotel_json=data_hotels, i=i)

        """Выводим результат в чат и базу данных"""
        if res != 'err':
            chat_info_hotel(message, res)
            rec_db_history(message, res)
        elif res == 'err':
            return res
    bot.send_message(message.chat.id, 'Запрос обработан')
    logger.info(f"Время выполнения запроса info_hotels: {time() - start_time}")


def chat_info_hotel(message: Any, data_info: Dict) -> None:
    """Выводим данные по отелю в чат
    :param message:
    :param data_info: - словарь данных по отелю"""

    if data_info['url_thumbs'] == 'thumb_err':
        with open('none_photo.png', 'rb') as img:
            bot.send_photo(message.chat.id, img)
    else:
        try:
            bot.send_photo(message.chat.id, data_info['url_thumbs'], timeout=5)
        except Exception:
            with open('none_photo.png', 'rb') as img:
                bot.send_photo(message.chat.id, img)

    bot.send_message(message.chat.id, f"- {data_info.get('name_hotel')}\n"
                                      f"- Город (поселок): {data_info.get('name_city')}\n"
                                      f"- Расстояние от центра: {data_info.get('distance_centre')}\n"
                                      f"- Ориентир: {data_info.get('name_landmarks')}\n"
                                      f"- {data_info.get('name_street')}\n"
                                      f"- Стоимость проживания: {data_info.get('amount_money')} руб.\n"
                                      f"  {data_info.get('info_amount_money')}\n"
                                      f"- ({data_info.get('price_day')} руб. за сутки)\n"
                                      f"- Сайт отеля: {data_info.get('url_hotel')}"
                     )
    photo_btn(message, id_hotel=data_info.get('id_hotel'), name_hotel=data_info.get('name_hotel'))


def rec_db_history(message: Any, data_info_db: Dict) -> None:
    """Записываем данные по пользователю и отелю в БД
    :param message:
    :param data_info_db: - словарь данных по отелю"""
    now = datetime.now()
    current_time = now.strftime("%Y:%m:%d - %H:%M:%S")
    id_user = message.chat.id
    command = data_dict(message.chat.id)[0].get('command')
    in_date = data_dict(message.chat.id)[0].get('ch_in')
    out_date = data_dict(message.chat.id)[0].get('ch_out')
    history_data.add_user_data(command=command, times=current_time, id_user=id_user,
                               name_hotel=data_info_db.get('name_hotel'),
                               city_name=data_info_db.get('name_city'),
                               city_landmarks=data_info_db.get('name_landmarks'),
                               city_street=data_info_db.get('name_street'),
                               dist_centre=data_info_db.get('distance_centre'),
                               in_date=in_date, out_date=out_date,
                               price_day=data_info_db.get('price_day'),
                               amount_money=data_info_db.get('amount_money'),
                               amount_info=data_info_db.get('info_amount_money'),
                               url_hotel=data_info_db.get('url_hotel')
                               )


def photo_btn(message: Any, id_hotel: int, name_hotel: str) -> None:
    """InLine кнопки для уточнения выбора (Да / Нет)
    :param message:
    :param id_hotel: - ID отеля
    :param name_hotel: - название отеля"""

    keybords.create_photo_btn(message, id_hotel)

    @bot.callback_query_handler(func=lambda call_photo: call_photo.data == str(id_hotel))
    def query_handler(call_photo: CallbackQuery) -> None:
        """Обработка callback кнопки 'Да'
        :param call_photo: - callback_data (ID отеля)"""

        bot.clear_step_handler_by_chat_id(chat_id=call_photo.message.chat.id)   # Очищаем от старого вызова
        z = rapidapi.HotelsApi.photo_hotel(message, id_hotel=id_hotel)
        if z == handlers.err_dict.get('tio'):
            bot.send_message(message.chat.id, handlers.err_dict.get('tio'))
            end(message)

        photo_data = data_dict(message.chat.id)[0].get('photo_search.json')

        numm_all_photo = len(photo_data['hotelImages'])
        bot.send_message(call_photo.message.chat.id,
                         f"Выберите количество фотографий отеля {name_hotel} для загрузки\n(не более 8 шт.):\n"
                         f"(всего доступно фото отеля {numm_all_photo} шт.)")
        bot.edit_message_reply_markup(call_photo.message.chat.id, call_photo.message.message_id)
        bot.register_next_step_handler(call_photo.message, req_photo, name_hotel)

    @bot.callback_query_handler(func=lambda call_cancel: call_cancel.data == str(101))
    def query_handler(call_cancel: CallbackQuery) -> None:
        """Обработка callback кнопки 'Нет'
        :param call_cancel: - callback_data (ничего не возвращает)"""

        bot.edit_message_reply_markup(call_cancel.message.chat.id, call_cancel.message.message_id)


def photo_hotel(message: Any, re_numm: int) -> None:
    """Обрабатываем словарь, ключ - photo_search.json с фото выбранного отеля
    :param message:
    :param re_numm: - количество фото отеля для загрузки"""

    photo_data = data_dict(message.chat.id)[0].get('photo_search.json')
    """Если ссылок в словаре меньше запрошенного количества, то уменьшаем re_numm"""
    if re_numm >= len(photo_data['hotelImages']):
        re_numm = len(photo_data['hotelImages'])
    """Правим ссылку"""
    for idx in range(re_numm):  # len - всего ссылок на картинки
        new_url = re.sub(r'{size}', r'z', photo_data['hotelImages'][idx]['baseUrl'])
        bot.send_photo(message.chat.id, new_url)
    logger.info(f"Всего фото данного отеля: {len(photo_data['hotelImages'])}")
    bot.send_message(message.chat.id, 'Запрос обработан')


def numm_photo_msg(message: Any, name_hotel: str) -> None:
    """Запрашиваем кол-во фото отеля далее переходим к функции req_photo
    :param message:
    :param name_hotel: - название отеля"""

    bot.send_message(message.chat.id, 'Выберите количество фото (до 8 шт.):')
    bot.register_next_step_handler(message, req_photo, name_hotel)


def req_photo(message: Any, name_hotel: str) -> None:
    """Обработка введенного значения фото
    :param message:
    :param name_hotel: - название отеля"""

    re_numm = handlers.numm_one(message.text)
    """Обработка исключений"""
    if re_numm == handlers.err_dict.get('err_numm'):
        bot.send_message(message.chat.id, handlers.err_dict.get('err_numm'))
        numm_photo_msg(message, name_hotel)
    else:
        bot.send_message(message.chat.id, f'Выбрано фото {re_numm} шт. для отеля:\n'
                                          f'{name_hotel}')
        photo_hotel(message, re_numm)


def user_history(message: Any) -> None:
    """Вывод в чат истории поиска оттелей из базы данных
        (пользователь видит только свою историю)
    :param message:"""

    data = history_data.select_data(message.chat.id)
    for i in range(len(data)):
        bot.send_message(message.chat.id, f"Введена команда:  {data[i].get('command')}\n"
                                          f"Выполнено:  {data[i].get('times')}\n"
                                          f"ID пользователя:  {data[i].get('id_user')}\n"
                                          f"{data[i].get('name_hotel')}\n"
                                          f"гор. {data[i].get('city_name')}\n"
                                          f"Ориентир: {data[i].get('city_landmarks')}\n"
                                          f"{data[i].get('city_street')}\n"
                                          f"{data[i].get('dist_centre')} от центра\n"
                                          f"Въезд:  {data[i].get('in_date')}\n"
                                          f"Выезд:  {data[i].get('out_date')}\n"
                                          f"Цена за сутки:  {data[i].get('price_day')} руб.\n"
                                          f"Всего за проживание:  {data[i].get('amount_money')} руб.\n"
                                          f"{data[i].get('amount_info')}\n"
                                          f"{data[i].get('url_hotel')}\n")

    # logger.info(f"\nПолучили словарь: {data_dict(message.chat.id)[1]}")
    bot.send_message(message.chat.id, 'Запрос завершен, для вывода команд нажмите "/help"')


def end(message: Any) -> None:
    """Last function
    :param message:"""

    # logger.info(f"\nПолучили словарь: {data_dict(message.chat.id)[1]}")
    bot.send_message(message.chat.id, 'Запрос завершен, для вывода команд нажмите "/help"')
