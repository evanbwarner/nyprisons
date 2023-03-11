#take pdfs from PDF_DIR folder, read using camelot, dump csv files to csv folder (one for each table)
#if pdf is image, then no output is produced

import camelot
import os

PDF_DIR = 'pdfs'
CSV_DIR = 'csvs'

if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR)
    
pdfnames = [name for name in os.listdir(PDF_DIR) if name.endswith('.pdf')]
pdfnames.sort()

for pdfname in pdfnames:
    pdfpath = os.path.join(PDF_DIR, pdfname)
    basename = pdfname.split('.')[0]
    initcsvname = os.path.join(CSV_DIR, basename + '-00.csv')
    if os.path.exists(initcsvname):
        print('File', initcsvname, 'already exists; no action taken to read', pdfname)
        continue
    
    print('Attempting to read', pdfname)
    tables = camelot.read_pdf(pdfpath, flavor='stream',pages = '1-end')
    print('Read', pdfname)
    numtables = len(tables)
    for i in range(numtables):
        print('   Reported accuracy for table', i, (tables[i].parsing_report)['accuracy'])
        stringi = str(i)
        if i < 10:
            stringi = '0' + stringi
        csvname = basename + '-' + stringi + '.csv'
        csvpath = os.path.join(CSV_DIR, csvname)
        frame = tables[i].df
        frame.to_csv(csvpath, index = False)
        print('   Written', csvname)