from bs4 import BeautifulSoup as bs
import re
from db import DB, Event, EventType, EventIs
import requests
from bs4 import BeautifulSoup
import json
import re

def race_types(cells):
    """
    Parse race type column in events row
    :param cells:
    :return:
    """
    race_cat = [t.strip() for t in cells[3].find_all(text=True) if 'Category - ' in t]
    race_type = [t.strip() for t in cells[3].find_all(text=True) if 'Category - ' not in t]
    return race_cat, race_type

def parse_event_row(row):
    getdata = dict()
    getdata['event_name'] = (lambda cells: cells[1].find('b').get_text().strip()) # event Name
    getdata['location'] = (lambda cells: cells[1].find(text = re.compile("^[a-zA-Z .]+, [A-Z]{2}")).strip())
    getdata['dates'] = (lambda cells: cells[1].find(text = re.compile("\s+\d{2}/\d{2}/\d{4}")).strip())
    getdata['flyer'] = (lambda cells: cells[1].find('a', href=True, text='Event Flyer')['href'])
    getdata['event_website'] = (lambda cells: cells[1].find('a', href=True, text='Event Website')['href'])
    getdata['permit_number'] = (lambda cells: cells[1].find(text=re.compile("\s+Permit Number:\s\S+")).strip().split(': ')[1])
    getdata['online_reg'] = (lambda cells: cells[1].find('a', href=True, text='Online Registration')['href'])
    getdata['promoter'] = (lambda cells: cells[2].find('a', href=True,).get_text().strip())
    getdata['director'] = (lambda cells: cells[2].find('a', href='javascript:void(0)',).get_text().strip())

    cells = row.find_all('td', recursive=False)
    rcat, rtype = race_types(cells)
    rowdata = dict()
    row['race_cat'] = rcat
    for key, l in getdata.items():
        try:
            rowdata[key] = l(cells)
        except:
            rowdata[key] = ''
    return rowdata, rtype

def load_events_past(page):
    """
    This is for bulk loading of events. This is not designed for updating the database.
    The html file data/events_94-15.html has all events available 1994 through the end of 2015
    :param htmlfile:
    :return:
    """
    s = bs(page, 'html.parser')

    row = s.find('table').find('tr')  # Search result row
    # print('*** {}'.format(row.get_text()))
    row = row.find_next_sibling() # Column header row
    # print('*** {}'.format(row.get_text()))

    for r in row.find_next_siblings(): #These are the event rows.
        if 'Try another search' not in r.get_text():
            rowdata, rtype = parse_event_row(r)
            try:
                if rowdata['event_name']:
                    ev = Event.create(**rowdata)
            except Exception as e:
                print(e)
            try:
                for t in rtype:
                    et, created = EventType.get_or_create(raceType=t)
                    EventIs.create(anEvent=ev, anEventType=et)
            except Exception as e:
                print(e)
                raise

def get_past_events(year):
    pass
