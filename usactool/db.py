from peewee import *
import datetime
import os


DB = SqliteDatabase('usac.db')

def DB_INIT(remove=False):
    """
    Nothing will happen with remove and loaddata set to false
    :param remove: Remove exisiting database
    :param loaddata: load data, into database, empty or not.
    :return: nothing
    """
    if remove:
        try:
            os.remove('usac.db')
        except:
            pass
        DB.connect()
        DB.create_tables([Event, EventIs, EventType])
    else:
        if os.path.isfile('usac.db'):
            DB.connect()
        else:
            DB.connect()
            DB.create_tables([Event, EventIs, EventType])


class BaseModel(Model):
    class Meta:
        database = DB

class Event(BaseModel):
    event_name = CharField(null=False) # Schedule SCH im Jefferson county
    location = CharField(null=True)
    state = CharField(null=True)
    dates = CharField(null=True)
    flyer = CharField(null=True)
    event_website = CharField(null=True)
    permit_number = CharField(null=True)
    online_reg = CharField(null=True)
    promoter = CharField(null=True)
    director = CharField(null=True)
    race_cat  = CharField(null=True)
    Timestamp = DateTimeField(default=datetime.datetime.now)


class EventType(BaseModel):
    raceType = CharField(null=False, unique=True)


class EventIs(BaseModel):
    """
    query = (Event
     .select()
     .join(EventIs)
     .join(EventType))
    """
    anEvent = ForeignKeyField(Event)
    anEventType = ForeignKeyField(EventType)

class RaceResults(BaseModel):
    race_id = CharField(null=False)
    medal = CharField(null=True)
    place = CharField(null=True)
    points = CharField(null=True)
    name = CharField(null=True)
    city_state = CharField(null=True)
    race_time = CharField(null=True)
    usac_number = CharField(null=True)
    bib = CharField(null=True)
    team = CharField(null=True)


class Laps(BaseModel):
    race_id = CharField(null=False)
    place = CharField(null=True)
    name = CharField(null=True)
    lap_1 = CharField(null=True)
    lap_2 = CharField(null=True)
    lap_3 = CharField(null=True)
    lap_4 = CharField(null=True)
    lap_5 = CharField(null=True)
    lap_6 = CharField(null=True)
    lap_7 = CharField(null=True)
    lap_8  = CharField(null=True)
    lap_9 = CharField(null=True)
    lap_10  = CharField(null=True)
