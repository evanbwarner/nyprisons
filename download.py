#read in list of urls from urls.csv and downloads each pdf dated 2013 or later to PDF_DIR

import os
import pandas
import http.cookiejar
import urllib.request
import time

PDF_DIR = 'pdfs'

month_dict = {
    'january': '01',
    'february': '02',
    'march': '03',
    'april': '04',
    'may': '05',
    'june': '06',
    'july': '07',
    'august': '08',
    'september': '09',
    'october': '10',
    'november': '11',
    'december': '12'
}

if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)
    
frame = pandas.read_csv('urls.csv')
frame['year'] = frame['urlnames'].str.split('-').str[4]
frame['time'] = frame['year'] + '-' + frame['urlnames'].str.split('-').str[3].map(month_dict) + '-01' #pandas time format

#Using the URLs, Download all of the Halt Incident Reports 
cookie_jar = http.cookiejar.CookieJar()

# Set the cookie jar in the request
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

for row in frame.itertuples():
    if not row.year.isdigit():
        print('Error: year string is not digit')
        continue
    elif int(row.year) < 2013:
        print('Year is before 2013; no download')
        continue
        
    filename = 'IPR' + row.time + '.pdf'
    filepath = os.path.join(PDF_DIR, filename)
    if os.path.exists(filepath):
        print('File', filename, 'already exists; no download')
        continue
    
    # Set a custom User-Agent and Referer header
    req = urllib.request.Request(row.urlnames)
    req.add_header("User-Agent", "Mozilla/5.0")
    #req.add_header("Referer", "doccs.ny.gov")

    # Send the request with the cookie jar
    try:
        response = opener.open(req)
        content = response.read()
    except:
        print('Could not download', row.urlnames)
        continue
        
    #check for a dead link
    try:
        decode = content.decode()
        if 'html' in content.decode().split('>')[0]:
            print('Dead link; no download')   
        else:
            print('Error: unusual file found; no download')
        continue
    except:
        pass
        
    #write the file
    with open(filepath, 'wb') as f:
        f.write(content)
    print('Downloaded', row.urlnames, 'to', filename)
    
    time.sleep(5)