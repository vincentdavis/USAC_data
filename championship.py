import requests
from bs4 import BeautifulSoup
import json
import csv

hdrs = {'User-Agent':
        'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
r = requests.session()
html_doc = r.get('http://www.usacycling.org/results/index.php?year=2016&id=2', headers=hdrs)
soup = BeautifulSoup(html_doc.text, 'html.parser')
for i in soup.findAll('a', onclick=True):
    print (i)
    req = i['onclick'].split('\'')[1]
    try:
        doc = r.get(req)
        print (doc)
    except ValueError:
        continue


# # write the data to .csv
# with open('nimes_assoc.csv', 'wb') as f:
#     csv.writer(f).writerows(assoc_table)