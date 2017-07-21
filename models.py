from peewee import *


DB_FILE = 'db/sodarecords.db'
db = SqliteDatabase(None)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True, primary_key=True)

class DrinkType(BaseModel):
    name = CharField(unique=True, primary_key=True)

class Purchase(BaseModel):
    buyer = ForeignKeyField(User, related_name='purchases')
    drink_type = ForeignKeyField(DrinkType, related_name='drink_types')
    num_cans = IntegerField()
    purchase_date = DateTimeField()

def verify_table():
    if not User.table_exists():
        User.create_table(True)
    if not DrinkType.table_exists():
        DrinkType.create_table(True)
    if not Purchase.table_exists():
        Purchase.create_table(True)

