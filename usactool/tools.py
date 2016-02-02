import re
import requests
from bs4 import BeautifulSoup as bs
import json

from usactool.db import Event, EventType, EventIs

def init_session():
    r = requests.session()
    HDRS = {'User-Agent':'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    # We have to load this page first or other pages return unauthorized access
    r.get('http://www.usacycling.org/results/index.php?year=2016&id=2', headers=HDRS)
    return r

def json_text(j):
    """
    Get text from Json
    :param j: response json
    :return: Beautifull soup object
    """
    return bs(json.loads(j.text)['message'], 'html.parser')

states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

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
    The html file data/events_page_example.html has all events available 1994 through the end of 2015
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

def get_past_events(start, end, states, files=True, savepages=''):
    """
    This will load past events from files or web.
    The savepages options save the html to files, or if files=True then reads from this location.
    Base URL example
    http://www.usacycling.org/events/?state=CO&race=&fyear=2015&rrfilter=rr

    :param year:
    :param files: folder containing files
    :return:
    """
    if not files: req = init_session()
    for year in range(start, end): #Get all past events
        for state in states:
            if not files:
                eventspage = req.get("http://www.usacycling.org/events/?state=" + state + "&race=&fyear=" + str(year) + "&rrfilter=rr" , headers=HDRS).text
                if '<small><sub>(200)</sub></small>' in eventspage.text: # we are not getting all the results on this page.
                    raise
                if savepages:
                    with open('{}events_{}_{}'.format(savepages, state, year), 'w') as f:
                        f.writer(eventspage)
            else:
                with open('{}events_{}_{}'.format(savepages, state, year), 'r') as f:
                    eventspage = f.read()
            load_events_past(eventspage)
