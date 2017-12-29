import re
import json
import time
import logging
import importlib

import requests
from bs4 import BeautifulSoup as bs

from usactool.db import Event, EventType, EventIs, DB, DB_INIT


importlib.reload(logging)
logging.basicConfig(filename='example.log', level=logging.WARNING)

HDRS = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

states1 = {"AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
           "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
           "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
           "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
           "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", 'CN', 'CS'}

states2 = {'IA', 'KS', 'UT', 'VA', 'NC', 'NE', 'SD', 'AL', 'ID', 'FM', 'DE', 'AK', 'CT', 'PR', 'NM', 'MS', 'PW', 'CO', 'NJ', 'FL', 'MN', 'VI', 'NV', 'AZ', 'WI', 'ND', 'PA', 'OK', 'KY', 'RI', 'NH',
           'MO', 'ME', 'VT', 'GA', 'GU', 'AS', 'NY', 'CA', 'HI', 'IL', 'TN', 'MA', 'OH', 'MD', 'MI', 'WY', 'WA', 'OR', 'MH', 'SC', 'IN', 'LA', 'MP', 'DC', 'MT', 'AR', 'WV', 'TX'}


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
    return bs(json.loads(j.text)['message'], 'html.parser')


def race_types(cells):
    """
    Parse race type column in events row
    :param cells:
    :return:
    """
    try:
        race_cat = [t.strip() for t in cells[3].find_all(text=True) if '^Category - ' in t]
    except:
        logging.error("race_cat error. Cell count = {}\n{}".format(len(cells), cells))
        # print("race_cat error:\n{}".format(cells))
        race_cat = ''
    try:
        race_type = [t.strip() for t in cells[3].find_all(text=True) if 'Category - ' not in t]
    except:
        logging.error("race_type error. Cell count = {}\n{}".format(len(cells), cells))
        # print("race_type error:\n{}".format(cells))
        race_type = ''
    return race_cat, race_type


def parse_event_row(row):
    getdata = dict()
    getdata['event_name'] = (lambda cells: cells[1].find('b').get_text().strip())  # event Name
    # getdata['location'] = (lambda cells: cells[1].find(text = re.compile("^[a-zA-Z ,./&-']+, [A-Z]{2}$")).strip())
    getdata['location'] = (lambda cells: cells[1].find(text=re.compile(', (' + '|'.join(states) + ")$")).strip())
    getdata['dates'] = (lambda cells: cells[1].find(text=re.compile("\s+\d{2}/\d{2}/\d{4}")).strip())
    getdata['flyer'] = (lambda cells: cells[1].find('a', href=True, text='Event Flyer')['href'])
    getdata['event_website'] = (lambda cells: cells[1].find('a', href=True, text='Event Website')['href'])
    getdata['permit_number'] = (lambda cells: cells[1].find(text=re.compile("\s+Permit Number:\s\S+")).strip().split(': ')[1])
    getdata['online_reg'] = (lambda cells: cells[1].find('a', href=True, text='Online Registration')['href'])
    getdata['promoter'] = (lambda cells: cells[2].find('a', href=True, ).get_text().strip())
    getdata['director'] = (lambda cells: cells[2].find('a', href='javascript:void(0)', ).get_text().strip())

    cells = row.find_all('td', recursive=False)
    assert (len(cells) == 4)
    rcat, rtype = race_types(cells)
    rowdata = dict()
    row['race_cat'] = rcat
    for key, l in getdata.items():
        try:
            rowdata[key] = l(cells)
        except:
            rowdata[key] = ''
    return rowdata, rtype


def get_past_events(start_yr, end_yr, states, get_page_from='URL', save_page='', delay=5):
    """
    This will load past events from files or web.
    Base URL example, they now call this the legacy page
    http://www.usacycling.org/events/?state=CO&race=&fyear=2015&rrfilter=rr

    :param year:
    :param get_page_from: folder containing files
    :return:
    """
    if get_page_from == 'URL':
        req = init_session()
    for year in range(start_yr, end_yr):  # Get all past events
        for state in states:
            if get_page_from == 'URL': # Load pages from the website.
                eventspage = req.get("http://legacy.usacycling.org/events/?state=" + state + "&race=&fyear=" + str(year) + "&rrfilter=rr", headers=HDRS).text
                if '<small><sub>(200)</sub></small>' in eventspage:  # we are not getting all the results on this page.
                    continue
                if save_page:
                    with open('{}events_{}_{}'.format(save_page, state, year), 'w') as f:
                        f.write(eventspage)
            elif get_page_from == 'FILE': # load data from already download pages
                try:
                    with open('{}events_{}_{}'.format(save_page, state, year), 'r') as f:
                        eventspage = f.read()
                except:
                    logging.error("no file state: {}, year: {}".format(state, year))
                    # print("no file state: {}, year: {}".format(state, year))
                    continue

            # Check if there are any events
            if "Sorry, no events were found." in eventspage:
                logging.warning("No events for state {} and year {}".format(state, year))
                # print("No events for state {} and year {}".format(state, year))
            else:
                load_events_past(eventspage, state)

            # Wait until loading the nex page
            time.sleep(delay)


def load_events_past(page, state, db_reset=False):
    """
    This is for bulk loading of events. This is not designed for updating the database.
    The html file data/events_page_example.html has all events available 1994 through the end of 2015
    :param htmlfile:
    :return:
    """
    DB_INIT(remove=db_reset)
    page = page.replace('<em>', '').replace('</em>', '').replace('&#x', ')')
    s = bs(page, 'html.parser')
    t = s.find('table')
    try:
        for r in t.find_all('tr', recursive=False):  # These are the event rows.
            if 'National Rankings System' not in r.get_text() and 'Event Information' not in r.get_text():
                if 'Try another search' not in r.get_text():
                    try:
                        rowdata, rtype = parse_event_row(r)
                        try:
                            if rowdata['event_name']:
                                rowdata['state'] = state
                                ev = Event.create(**rowdata)
                        except Exception as e:
                            logging.error(e)
                            print(e)
                        try:
                            for t in rtype:
                                et, created = EventType.get_or_create(raceType=t)
                                EventIs.create(anEvent=ev, anEventType=et)
                        except Exception as e:
                            print(e)
                            logging.error(e)
                            raise
                    except Exception as e:
                        logging.error(r.find_all('td', recursive=False))
                        print(e)
                        raise
    except Exception as e:
        logging.error(2)
        print(s)


def get_racer_results(licence, get_page_from='FILE', req=False):
    """
    http://www.usacycling.org/results/index.php?compid=124587
    :param licence:
    :return:
    """
    if get_page_from == 'URL':
        req = init_session()
    resultspage = req.get("http://www.usacycling.org/results/index.php?compid=" + licence, headers=HDRS).text
    return resultspage


def get_results(race_id):
    """
    Takes ID of a race and yields result table rows one by one

    """
    req = init_session()
    # Define headers
    headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Host": "legacy.usacycling.org",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
    }
    # Get response from the race URL
    race_url = "http://legacy.usacycling.org/results/index.php?ajax=1&act=loadresults&race_id={0}".format(race_id)
    r = req.get(race_url, headers=headers)
  	# Parse response JSON and get the results table
    table_html = json.loads(r.text)["message"]
    results_table = bs(table_html, 'html.parser').div
    # Define rows with data and iterate through them
    results_rows = results_table.find_all("div", recursive=False)[1:]
    for results_row in results_rows:
        row_dict = {}
        # define data cells for each row
        data_cells = results_row.find_all("div", recursive=False)
        try:
            row_dict["medal"] = data_cells[0].img["title"].strip()
        except (AttributeError, TypeError, KeyError):
            row_dict["medal"] = ""
        try:
            row_dict["place"] = data_cells[1].text.strip()
        except IndexError:
            row_dict["place"] = ""
        try:
            row_dict["points"] = data_cells[2].text.strip()
        except IndexError:
            row_dict["points"] = ""
        try:
            row_dict["name"] = data_cells[4].text.strip()
        except IndexError:
            row_dict["name"] = ""
        try:
            row_dict["city, state"] = data_cells[5].text.strip()
        except IndexError:
            row_dict["city, state"] = ""
        try:
            row_dict["time"] = data_cells[6].text.strip()
        except IndexError:
            row_dict["time"] = ""
        try:
            row_dict["usac #"] = data_cells[8].text.strip()
        except IndexError:
            row_dict["usac #"] = ""
        try:
            row_dict["bib"] = data_cells[9].text.strip()
        except IndexError:
            row_dict["bib"] = ""
        try:
            row_dict["team"] = data_cells[10].text.strip()
        except IndexError:
            row_dict["team"] = ""

        yield row_dict


def get_lap_times(race_id):
    """
    Takes ID of a race and yields lap times rows one by one

    """
    req = init_session()
    # Define headers
    headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Host": "legacy.usacycling.org",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
    }
    # Get response from the race URL
    race_url = "https://legacy.usacycling.org/results/index.php?ajax=1&act=splits&race_id={0}".format(race_id)
    r = req.get(race_url, headers=headers)
    # Parse response and get the laps time page
    laps_page = bs(r.text, 'html.parser')
    # Parse the page and get lap times table
    laps_table = laps_page.find("table", class_="datatable")
    try:
        laps_rows = laps_table.find_all("tr")[1:]
        if not laps_rows:
            raise AttributeError
    except (AttributeError, IndexError):
        yield "There is no lap times data for that race"
    # Iterate through data rows and extract data
    for laps_row in laps_rows:
        row_dict = {}
        # define data cells for each row
        data_cells = laps_row.find_all("td", recursive=False)
        try:
            row_dict["place"] = data_cells[0].text.strip()
        except (IndexError, KeyError):
            row_dict["place"] = ""
        try:
            row_dict["name"] = data_cells[1].text.strip()
        except (IndexErrnameor, KeyError):
            row_dict["name"] = ""

        # Define lap times
        column_index = 2
        lap_number = 1
        while True:
            try:
                row_dict["Lap {0}".format(lap_number)] = data_cells[column_index].text.strip()
            except (IndexError, AttributeError):
                break

            column_index += 1
            lap_number += 1

        yield row_dict
