from typing import Any, Dict
from loguru import logger
from requests import request
from json import loads
from time import time
import handlers
import loader


class HotelsApi:
    """Класс запросов данных API Hotels.com"""
    def __init__(self, f_city: str):
        """
        __init__
        :param f_city: название города
        """

        self.f_city = f_city

    def query_city(self, message: Any) -> str:
        """Получение объекта Response для города
        :param message:"""

        url = "https://hotels4.p.rapidapi.com/locations/v2/search"

        querystring = {"query": self.f_city, "locale": "ru_RU", 'currency': 'RUB'}

        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': loader.key_hotel
        }
        """Запрашиваем данные и записываем в файл json"""
        z = check_request(message, url=url, headers=headers, querystring=querystring,
                          name_json='city_search.json')
        if z == handlers.err_dict.get('tio'):
            return handlers.err_dict.get('tio')

    @classmethod
    def query_hotel(cls, message: Any, id_city: int, numm_hotels: int, check_in: str, check_out: str,
                    min_price: int = None, max_price: int = None, sort_order: str = None) -> str:
        """Запрашиваем данные, получаем объект Response по отелям
        :param message:
        :param id_city: - ID города
        :param numm_hotels: - количество отелей
        :param check_in: - дата въезда
        :param check_out: - дата выезда
        :param min_price: - минимальная цкеа
        :param max_price: - максимальная цена
        :param sort_order: - порядок сортировки"""

        url = "https://hotels4.p.rapidapi.com/properties/list"

        querystring = {"destinationId": id_city, "pageSize": numm_hotels,
                       "checkIn": check_in, "checkOut": check_out,
                       "priceMin": min_price, "priceMax": max_price, "sortOrder": sort_order,
                       "locale": "ru_RU", "currency": "RUB"}    # RUB - вывод в рублях (USD - $)

        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': loader.key_hotel
        }
        """Запрашиваем данные и записываем в файл json"""
        z = check_request(message, url=url, headers=headers, querystring=querystring,
                          name_json='hotels_search.json')
        if z == handlers.err_dict.get('tio'):
            return handlers.err_dict.get('tio')

    @classmethod
    def photo_hotel(cls, message: Any, id_hotel: int) -> str:
        """Запрашиваем данные, получаем объект Response по фото отеля
        :param message:
        :param id_hotel: - ID отеля"""

        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

        querystring = {"id": str(id_hotel)}

        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': loader.key_hotel
        }
        """Запрашиваем данные и записываем в файл json"""
        z = check_request(message, url=url, headers=headers, querystring=querystring,
                          name_json='photo_search.json')
        if z == handlers.err_dict.get('tio'):
            return handlers.err_dict.get('tio')


def check_request(message, url: str, headers: Dict, querystring: Dict, name_json: str) -> str:
    """Получение данных от api hotels
    :param message: - from_iser
    :param url: - https ссылка на запрашиваемый объект
    :param querystring: - параметры запроса
    :param headers: - заголовок запроса
    :param name_json: - имя выходного файла"""

    start_time = time()
    """Информационное сообщение для пользователя"""
    loader.bot.send_message(message.chat.id, 'Идет обработка запроса ...')
    try:
        """Запрашиваем данные, получаем объект Response"""
        response = request("GET", url, headers=headers, params=querystring, timeout=(6, 17))
        logger.info(f"Статус код: <Response [{response.status_code}]>")

        """Если статус код не 200 (Ок), то завершаем запрос"""
        if response.status_code != 200:
            logger.error(f"Ошибка обработки запроса, статус код: <Response [{response.status_code}]>")
            loader.end(message)

        try:
            """Парсим и записываем в словарь json"""
            data = loads(response.text)
        except Exception as jsn:
            """Печать в консоль"""
            logger.error(f"Ошибка обработки JSON: {jsn}")
            loader.end(message)
            return loader.bot.send_message(message.chat.id, 'Ошибка обработка запроса ...')

        loader.data_dict(message.chat.id)[0][name_json] = data  # Пишем сериализованный объект в словарь

        logger.info(f"Время выполнения запроса: {time() - start_time}")
    except (Exception, ConnectionError) as tio:
        """Печать в консоль"""
        logger.error(f"Превышено время ожидания запроса: {tio}")
        return "Превышено время ожидания запроса"
