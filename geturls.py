#creates a csv file urls.csv in same directory containing full urls for all Incarcerated Profile Reports available at https://doccs.ny.gov/research-and-reports

import requests
from bs4 import BeautifulSoup
import time
import pandas

#as of 2/24/23 there are 57 pages of reports, but check https://doccs.ny.gov/research-and-reports to see if more are needed
NUM_PAGES = 60

#extract all of the urls using an ajax call which populates each page, transform the response to the request into a json, then pull the html
def extract_urls(pages):
    all_urls = []
    for num in range(pages):
        response = requests.get(f'https://doccs.ny.gov/research-and-reports?q=/research-and-reports&page={num}&_wrapper_format=drupal_ajax')
        info = response.json()
        html = info[4]['data']
        soup = BeautifulSoup(html, features='lxml')
        for link in soup.find_all('a'):
            all_urls.append(link.get('href'))
    return all_urls

urlsdup = extract_urls(NUM_PAGES)

#get rid of duplicates
urls = []
[urls.append(url) for url in urlsdup if url not in urls]

#Remove all urls which contain "research-and-reports", as these are not links for the reports, but for the pages within the website.
urls = [url for url in urls if 'research-and-reports' not in url]

#Remove all urls that are not incarcerated profile reports
urls = [url for url in urls if 'incarcerated-profile-report' in url]

#add header to urls
urls = ['https://doccs.ny.gov' + url for url in urls]

print(urls)

urldf = pandas.DataFrame(urls, columns=['urlnames'])

urldf.to_csv('urls.csv')