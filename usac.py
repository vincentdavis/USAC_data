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
    DB.connect()
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
    # getdata['dir_email'] = (lambda cells: cells[2].find_all('a')[2])
    getdata['race_cat'] = (lambda cells: cells[3].find(text=re.compile("Category - \w")).strip()[-1])

    r = init_session()
    eventspage = r.get("http://www.usacycling.org/events/?zipcode=" + str(zipcode)+"&radius=" + str(radius) + "&race=&fyear=" + str(year) + "&rrfilter=rr" , headers=HDRS)
    s = BeautifulSoup(eventspage.text, 'html.parser')
    row = s.find('table').find('tr')  # Search result row
    # print('*** {}'.format(row.get_text()))
    row = row.find_next_sibling() # Column header row
    # print('*** {}'.format(row.get_text()))
    #These are the event rows.
    for r in row.find_next_siblings():
        rowdata = dict()
        cells = r.find_all('td', recursive=False)
        for key, l in getdata.items():
            try:
                rowdata[key] = l(cells)
            except:
                rowdata[key] = ''
        try:
            if rowdata['permit_number']:
                e = Event.create(**rowdata)
        except Exception as e:
            print(e)
            print(rowdata)


