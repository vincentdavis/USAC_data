import requests
from bs4 import BeautifulSoup
import json

HDRS = {'User-Agent':'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
r = requests.session()
# We have to load this page first or other pages return unauthorized access
startpage = r.get('http://www.usacycling.org/events/rr.php', headers=HDRS)

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
    :param event_id: number representing event.
    :return: dict {'name':'', 'races':{name, number}} or None if no event
    """
    event = json_text(r.get('http://www.usacycling.org/results/index.php?ajax=1&act=infoid&info_id='+str(e), headers=HDRS))
    if "No results found." not in event:
        #print('Race is: {} and race name is: {}'.format(e, race.find('h3').getText()))
        info = {'name': event.find('h3').getText(), 'races':{}}
        for a in event.find_all('li'):
            info['races'][a.find('a').contents[0]] = a.get('id')

        for a in race.find_all('li'):
            print('---- {}'.format(a.find('a').contents[0])) # get the text from the href
            print('    ---- {}'.format(a.get('id'))) # get the id tage value
            results = r.get('https://www.usacycling.org/results/index.php?ajax=1&act=loadresults&race_id=955427', headers=hdrs)
            splits = r.get('https://www.usacycling.org/results/index.php?ajax=1&act=splits&race_id=955427', headers=hdrs)
    else:
        return None