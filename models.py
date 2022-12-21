from peewee import Model, SqliteDatabase, TextField, CharField, IntegerField, FloatField

db = SqliteDatabase('history.db')


class HistorySearch(Model):
    """Создаем модель HistorySearch для хранения истории поиска отелей"""
    command = CharField(null=False)
    times = CharField(null=False)
    id_user = IntegerField(null=False)
    name_hotel = CharField(null=True)
    city_name = CharField(null=True)
    city_landmarks = CharField(null=True)
    city_street = CharField(null=True)
    dist_centre = CharField(null=True)
    in_date = CharField(null=False)
    out_date = CharField(null=False)
    price_day = FloatField(null=True)
    amount_money = FloatField(null=True)
    amount_info = CharField(null=True)
    url_hotel = TextField(null=True)

    class Meta:
        database = db  # модель будет использовать базу данных 'history.db'
