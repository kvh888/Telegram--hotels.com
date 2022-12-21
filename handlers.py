from typing import Any, List, Dict, Union
from loguru import logger
import re
import loader

"""Словарь основных ошибок"""
err_dict = {'err_city': 'Город не найден, попробуйте еще раз',
            'tio': 'Превышено время ожидания запроса',
            'err_numm': 'Введено не число, попробуйте еще раз',
            'err_range': 'Не диапазон чисел',
            'err_date': 'Ошибка: Дата выезда ранее даты въезда'
            }


def city_id(message: Any):
    """Функция получения destinationId (ID города) из "CITY_GROUP",
     из словаря пользователя, ключ - city_search.json
    :param message:"""

    city_lst = []

    res = loader.data_dict(message.chat.id)[0].get('city_search.json')

    try:
        for idx in range(len(res['suggestions'][0]['entities'])):
            """Заполняем словарь найденными ID (caption)"""
            z_dest = int(res['suggestions'][0]['entities'][idx]['destinationId'])
            z_name = res['suggestions'][0]['entities'][idx]['caption']
            """Убираем все лишнее из названий"""
            re_z_name = re.sub(r'<.*?>', r'', z_name)
            city_lst.append([z_dest, re_z_name])
        try:
            """Проверка, что город существует (деление на длину пустого списка)"""
            1 / len(city_lst)
        except ZeroDivisionError:
            return err_dict.get('err_city')

        return city_lst
    except Exception as err:
        return 'Ошибка загрузки города:', err


def numm_one(numm_data: Any) -> Union[int, str]:
    """Проверка на корректность ввода, при возможности выделение числа (одного) (str)
    :param numm_data: - строка из которой нужно получить одно число"""

    try:
        numm_data = re.findall(r'\d+', numm_data)[0]
        """Вводим ограничение на max введенного значения"""
        if int(numm_data) > 8:
            numm_data = 8
            logger.info(f"Количество отелей: {numm_data}")
            return numm_data
        else:
            return int(numm_data)
    except IndexError:
        err_numm = err_dict.get('err_numm')
        return err_numm


def numm_range(numm_data: Any) -> Union[List, str]:
    """Проверка на корректность ввода диапазона чисел (2 числа), при возможности выделение числа (str)
    :param numm_data: - строка из которой нужно получить два числа"""

    str_two_digit = re.findall(r'\d+', numm_data)[0:2]
    if len(str_two_digit) == 0:
        """Если выделить число не удалось возвращаем код ошибки"""
        err_range = err_dict.get('err_range')
        return err_range
    elif len(str_two_digit) == 1:
        """Если введено 1 число, то оно будет считаться MIN, MAX=1000000"""
        str_two_digit.append('1000000')

    numm_two_digit = [int(i) for i in str_two_digit]
    """Сортируем введенные значения по возрастанию (для этого тип str  меняем на int)"""
    return sorted(numm_two_digit)


def check_date(date_1: str, date_2: str) -> str:
    """Проверка, что вторая введенная дата позднее или равна первой
    :param date_1: - дата въезда
    :param date_2: - дата выезда"""

    numm_1 = re.findall(r'\d+', date_1)[0:3]
    numm_2 = re.findall(r'\d+', date_2)[0:3]
    if int(numm_1[0]) >= int(numm_2[0]) and int(numm_1[1]) > int(numm_2[1]) \
            or int(numm_2[0]) - int(numm_1[0]) > 1:
        """Если условие не выполнено возвращаем код ошибки (err)"""
        return 'err'
    elif int(numm_1[1]) >= int(numm_2[1]) and int(numm_1[2]) > int(numm_2[2]) \
            and int(numm_1[0]) == int(numm_2[0]):
        """Если условие не выполнено возвращаем код ошибки (err)"""
        return 'err'


def check_command(sel_command: Dict) -> str:
    """Действия для комманд lowprice, highprice, bestdeal
    :param sel_command: - словарь пользователя"""

    if sel_command['command'] == '/lowprice':
        sel_command['sort_order'] = 'PRICE'
        sel_command['min_dist'] = None
        sel_command['max_dist'] = None
        return 'low'
    elif sel_command['command'] == '/highprice':
        sel_command['sort_order'] = 'PRICE_HIGHEST_FIRST'
        sel_command['min_dist'] = None
        sel_command['max_dist'] = None
        return 'high'
    elif sel_command['command'] == '/bestdeal':
        sel_command['sort_order'] = 'DISTANCE_FROM_LANDMARK'
        return 'best'


def idx_select(message, sel_distantion: Dict) -> Union[List, str]:
    """Выбираем количество отелей в зависимости от диапазона расстояний
    :param message:
    :param sel_distantion: - словарь пользователя"""
    min_dist = sel_distantion.get('min_dist')
    max_dist = sel_distantion.get('max_dist')

    if (min_dist and max_dist) is None:
        """Условия для команд lowprice / highprice"""
        numms = (sel_distantion['numm_hotels'] - 1)
        idx_lst = [i for i in range(numms)]

    else:
        """Условие для команды bestdeal"""
        idx_lst = idx_range(message, min_dist=min_dist, max_dist=max_dist)

        """Ограничиваем количество выводимых отелей"""
        if len(idx_lst) > 8:
            idx_lst = idx_lst[:8]

        """Ограничиваем список введенным количеством отелей"""
        numms = (sel_distantion['numm_hotels'] - 1)
        idx_lst = idx_lst[:numms]

    try:
        idx_lst[0]
    except IndexError:
        logger.error(f"Нет данных для выбора")
        return 'err'
    logger.info(f"Диапазон индексов для вывода: {idx_lst}")
    return idx_lst


def idx_range(message: Any, min_dist: int = 0, max_dist: int = 100) -> List:
    """Получение индексов списка отелей для одинаковых расстояний с минимальной ценой,
    а так же индексов уникальных расстояний
    :param message:
    :param min_dist: - минимальное расстояние до центра
    :param max_dist: - максимальное расстояние до центра"""

    data_dist = loader.data_dict(message.chat.id)[0].get('hotels_search.json')
    """Множество элементов всего списка"""
    idx_init = set()
    """Множество элементов с одинаковыми расстояниями"""
    idx_set = set()
    """Список множеств с одинаковыми расстояниями"""
    idx_lst = []
    for i in range(len(data_dist['data']['body']['searchResults']['results']) - 1):
        """Преобразуем в число текущее значение расстояния"""
        z_0 = data_dist['data']['body']['searchResults']['results'][i]['landmarks'][0]['distance']
        z_re_0 = re.sub(r' км', r'', z_0)  # Удаляем 'км'
        z_re_0 = float(re.sub(r',', r'.', z_re_0))  # Заменяем ',' на '.'
        """Преобразуем в число следующее значение расстояния"""
        z_1 = data_dist['data']['body']['searchResults']['results'][i + 1]['landmarks'][0]['distance']
        z_re_1 = re.sub(r' км', r'', z_1)  # Удаляем 'км'
        z_re_1 = float(re.sub(r',', r'.', z_re_1))  # Заменяем ',' на '.'
        """Выбираем индексы отелей соответствующих условию диапазона (min_dist - max_dist)"""
        if min_dist <= z_re_0 <= max_dist:
            """Собираем множество индексов для одинаковых расстояний"""
            if z_re_0 == z_re_1:
                idx_set.add(i)
                idx_set.add(i + 1)
            else:
                if idx_set != set():
                    """Список множеств индексов с одинаковыми расстояниями"""
                    idx_lst.append(idx_set)
                idx_set = set()
            idx_init.add(i)

    logger.info(f"idx_init = {idx_init} - все индексы отелей (по условию) "
                f"из {len(data_dist['data']['body']['searchResults']['results'])}")
    logger.info(f"idx_lst = {idx_lst} - список множеств индексов отелей с одинаковыми расстояниями")
    unic_dist = set()
    """Множество с индексами уникальных расстояний"""
    for i in range(len(idx_lst)):
        unic_dist = unic_dist ^ idx_lst[i]
    unic_dist = unic_dist ^ idx_init
    logger.info(f"unic_dist = {unic_dist} - индексы отелей с уникальными расстояниями")

    """Множество индексов для одинаковых расстояний с минимальной ценой"""
    min_price_range = set()
    for j in range(len(idx_lst)):
        """Задаем максимальное значение цены и переменную индекса"""
        summ_0 = 10e7
        idx = 0  # без нее PyCharm выдает предупреждение, что i может быть изменена
        for i in list(idx_lst[j]):
            summ = data_dist['data']['body']['searchResults']['results'][i]['ratePlan']['price']['exactCurrent']
            if summ_0 > summ:
                summ_0 = summ
                idx = i
            logger.info(f"индекс - цена: {i} - {summ}")
        logger.info(f"Результат - для равного расст. min цена (индекс - цена): {idx} - {summ_0}")
        min_price_range.add(idx)
    logger.info(f"min_price_range = {min_price_range} - объединяем полученные индексы во множество")
    """Добавляем полученные индексы к индексам уникальных расстояний
        и преобразуем множество в список"""
    result = sorted(list(min_price_range | unic_dist))
    logger.info(f"{result} - список индексов (unic_dist + min_price_range) удовлетворяющих условию bestdeal")
    return result


def hotel_dict(hotel_json: Dict, i: int) -> Union[Dict, str]:
    """Определяем переменные для вывода в чат и обрабатываем исключения
    :param hotel_json: - словарь полученных отелей
    :param i: - индекс списка отелей (из loader.py)"""

    info_hotel_dict = dict()
    """Определяем переменные для вывода в чат и обрабатываем исключения"""
    try:
        info_hotel_dict['id_hotel'] = \
            (hotel_json['data']['body']['searchResults']['results'][i]['id'])

        info_hotel_dict['name_hotel'] = \
            (hotel_json['data']['body']['searchResults']['results'][i]['name'])

        info_hotel_dict['name_city'] = \
            (hotel_json['data']['body']['searchResults']['results'][i]['address']
             ['locality'])

        info_hotel_dict['name_landmarks'] = \
            (hotel_json['data']['body']['searchResults']['results'][i]['landmarks']
             [0]['label'])

        try:
            info_hotel_dict['name_street'] = \
                (hotel_json['data']['body']['searchResults']['results']
                 [i]['address']['streetAddress'])
        except KeyError:
            info_hotel_dict['name_street'] = 'ул. адрес отсутствует'

        info_hotel_dict['distance_centre'] = \
            (hotel_json['data']['body']['searchResults']['results'][i]['landmarks'][0]
             ['distance'])

        info_hotel_dict['amount_money'] = \
            (hotel_json['data']['body']['searchResults']['results'][i]['ratePlan']
             ['price']['exactCurrent'])

        info_hotel_dict['info_amount_money'] = \
            (hotel_json['data']['body']['searchResults']['results'][i]['ratePlan']
             ['price']['info'])

        info_hotel_dict['url_hotel'] = \
            f"https://ru.hotels.com/ho{(hotel_json['data']['body']['searchResults']['results'][i]['id'])}"

        """Получаем количество дней проживания в отеле и цена за сутки"""
        try:
            numm_days = int(re.findall(r'\d+', info_hotel_dict.get('info_amount_money'))[1])
            info_hotel_dict['price_day'] = round(info_hotel_dict.get('amount_money') / numm_days)
        except IndexError as days_err:
            logger.error(f"Ошибка обработки запроса по отелю: {days_err}")
            return 'err'

        """Проверяем наличие миникартинки отеля"""
        try:
            info_hotel_dict['url_thumbs'] = \
                (hotel_json['data']['body']['searchResults']['results'][i]
                 ['optimizedThumbUrls']['srpDesktop'])
        except (IndexError, KeyError):
            info_hotel_dict['url_thumbs'] = 'thumb_err'

    except (IndexError, KeyError, TypeError, AttributeError) as info_err:
        logger.error(f"Ошибка обработки запроса по отелю: {info_err}")
        if info_err == 'info':
            logger.error(f"Отсутствует цена проживания для выбранных дат\n"
                         f"возможно из-за слишком большого диапазона дат")
        return 'err'

    return info_hotel_dict
