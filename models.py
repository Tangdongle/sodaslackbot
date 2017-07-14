from peewee import *

DB_FILE = 'db/sodarecords.db'

db = SqliteDatabase(DB_FILE)

class User(Model):
    username = CharField(unique=True, primary_key=True)

    class Meta:
        database = db

class DrinkType(Model):
    name = CharField(unique=True, primary_key=True)

    class Meta:
        database = db

class Purchase(Model):
    buyer = ForeignKeyField(User, related_name='purchases')
    drink_type = ForeignKeyField(DrinkType, related_name='drink_types')
    num_cans = IntegerField()
    purchase_date = DateTimeField()

    class Meta:
        database = db
