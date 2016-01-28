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

class BaseModel(Model):
    class Meta:
        database = DB

class Event(BaseModel):
    event_name = CharField(null=False) # Schedule SCH im Jefferson county
    location = CharField(null=True)
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