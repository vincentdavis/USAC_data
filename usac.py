from db import DB, Event
import requests
from bs4 import BeautifulSoup
import json
import re


HDRS = {'User-Agent':'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

def init_session():
    r = requests.session()
    # We have to load this page first or other pages return unauthorized access
    r.get('http://www.usacycling.org/results/index.php?year=2016&id=2', headers=HDRS)
    return r

def json_text(j):
    """
    Get text from Json
    :param j: response json
    :return: Beautifull soup object
    """
    return BeautifulSoup(json.loads(j.text)['message'], 'html.parser')

def get_event(session, event_id):
    """
    Get event details. I think each day is an event for multi day events like CX nationals
    :param session: Requests session that has been initiated at usac
    for example, get_event(r, 94310)

    :param event_id: number representing event.
    :return: dict {'name':'', 'races':{name, number}} or None if no event
    """
    page = session.get('http://www.usacycling.org/results/index.php?ajax=1&act=infoid&info_id='+str(event_id), headers=HDRS)
    # print(page.text)
    event = json_text(page)
    if "No results found." not in event:
        #print('Race is: {} and race name is: {}'.format(e, race.find('h3').getText()))
        info = {'name': ''.join(t for t in event.find('h3').find_all(text=True)), 'races':{}}
        for a in event.find_all('li'):
            info['races'][a.find('a').contents[0]] = a.get('id').split()
        return info
    else:
        return None

def get_event_list(year, zipcode=80919, radius=10000):
    """

    """
    req = init_session()
    eventspage = req.get("http://www.usacycling.org/events/?zipcode=" + str(zipcode)+"&radius=" + str(radius) + "&race=&fyear=" + str(year) + "&rrfilter=rr" , headers=HDRS)
    load_events()







