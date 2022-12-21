from typing import List
import models

"""Если таблица не существует, то создаем ее"""
models.HistorySearch.create_table()


def add_user_data(command: str, times: str, id_user: int, name_hotel: str, city_name: str,
                  city_street: str, city_landmarks: str, dist_centre: str, in_date: str,
                  out_date: str, price_day: float, amount_money: float,
                  amount_info: str, url_hotel: str) -> None:
    """Добавление данных по запрошенному отелю в таблицу БД db
    :param command: - введенная команда
    :param times: - дата и время выполнения запроса
    :param id_user: - ID пользователя
    :param name_hotel: - название отеля
    :param city_name: - название города
    :param city_landmarks: - название района
    :param city_street: - название улицы
    :param dist_centre: - расстояние от центра
    :param in_date: - дата въезда
    :param out_date: - дата выезда
    :param price_day: - цена за 1 день
    :param amount_money: - сумма за время проживания
    :param amount_info: - коментарий к amount_money
    :param url_hotel: - URL ссылка отеля
    """
    with models.db:
        models.HistorySearch.create(
            command=command,
            times=times,
            id_user=id_user,
            name_hotel=name_hotel.strip(),
            city_name=city_name.strip(),
            city_landmarks=city_landmarks.strip(),
            city_street=city_street.strip(),
            dist_centre=dist_centre.strip(),
            in_date=in_date,
            out_date=out_date,
            price_day=price_day,
            amount_money=amount_money,
            amount_info=amount_info.strip(),
            url_hotel=url_hotel.strip()
        )


def select_data(user: int) -> List:
    """Формируем список словарей записей БД, фильтруем выборку по ID пользователя
    :param user: - ID пользователя"""

    with models.db:
        info = models.HistorySearch.select().filter(id_user=user)
        data_lst = []
        for req in info:
            data_lst.append({
                'command': req.command,
                'times': req.times,
                'id_user': req.id_user,
                'name_hotel': req.name_hotel,
                'city_name': req.city_name,
                'city_landmarks': req.city_landmarks,
                'city_street': req.city_street,
                'dist_centre': req.dist_centre,
                'in_date': req.in_date,
                'out_date': req.out_date,
                'price_day': req.price_day,
                'amount_money': req.amount_money,
                'amount_info': req.amount_info,
                'url_hotel': req.url_hotel,
            })
    return data_lst
