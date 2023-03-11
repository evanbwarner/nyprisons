# nyprisons
working with some messy data on NYS prisons

Here is some code to scrape and clean data from New York State Incarcerated Profile Reports (IPRs), available at https://doccs.ny.gov/research-and-reports. All code is written in Python 3, with the package Camelot to read pdfs and the package pandas to manage data tables. Some code in geturls.py and download.py is taken with modifications from https://github.com/moogilybear/halt_incident_reports.

1. geturls.py finds a list of urls on https://doccs.ny.gov/research-and-reports corresponding to IPRs and writes to a file urls.csv.
2. download.py downloads the Incarcerated Profile Report corresponding to each url in urls.csv and places the pdfs in a directory pdfs. If the year is earlier than 2013 we do not bother to download, as the relevant pdfs will not be readable (see below).
3. convert.py goes through the pdfs in the directory pdfs and applies Camelot to extract pandas dataframes for each table. Each dataframe is written to a csv file and placed in the directory csvs. The flavor 'stream' is used for Camelot, since the tables in the IPRs do not generally have separating lines. No further manual customization is used, since the format of the tables in the IPRs varies somewhat.
4. The real work occurs in clean.py, which attempts to build relatively clean tables based on Camelot's very messy output. Pandas dataframes are read in from the csv files in the directory csvs and the cleaned tables are written to csv files in the directory cleancsvs. The cleaning process roughly consists in the following steps:
a) We attempt to determine the type of table under consideration (e.g., Age, Ethnicity, etc.). Most of the time, this information is contained in a header which gets picked up by Camelot. Some of the time this does not work, and we instead look for certain key words. If all else fails (for example, sometimes the table is a continuation of a previous table and has very few columns), we assume it is a continuation of a previous table. We have a list of tables that are all of approximately the same form that we can deal with, and if our table is not of this form we do not attempt to clean it.
b) We clean the column headers. Sometimes these are spread over multiple rows, and sometimes there are extraneous columns containing no useful information that have to be merged with nearby columns.
c) We clean the row headers/rows. The facility types (e.g. "MAXIMUM SECURITY") are sometimes placed in their own column and sometimes not; these need to be read off and remembered. Then extraneous rows need to be merged with nearby rows, which is the subtlelest part of the cleaning process.
d) We check the data against the totals provided column by column, to certify that each column that has been read is complete.
e) We assign MultiIndexes to the data (both rows and columns) to store facility type, date, and table number data.
5. consolidate.py loads in all csv files in cleancsvs and combines them into one large csv file, which is written to data.csv.
6. Finally, read.py illustrates a few simple methods of accessing and plotting some of the data in data.csv.

The resulting data is still messy in various ways, which we describe now as outstanding problems, some of which are potentially solvable.
1) All pdfs before 2013, as well as 2013-06, are stored as images rather than as text and are inaccessible to Camelot.
2) Camelot does not always read the tables at all, and when it does it does not always read the whole table. When this happens the code does not attempt to clean the partial data.
3) The IPR for 2018-12 is in a different format that is not properly handled by clean.py, and we do not attempt to clean its data.
4) Our method for detecting the end of the column headers (finding the value of columnheaderend in clean.py) does not work on certain tables in the most recent IPRs, and will have to be replaced with a new method (right now the code does not attempt to read those tables).
5) There are issues with merging rows that are currently dealt with in an ad hoc way. They could be handled intelligently if the program kept track of "expected" facility names over time and resolved conflicts so as to create an output closest to expected.
6) There are a couple of odds and ends that seem like they have to be resolved manually; for example, see some screwed-up headers in 2019-05-01-18.
7) Long facility names and column headers need to be manually "mapped" to one another; e.g., "EDGECOMBE-F WORK REL" and "EDGECOMBEF WORK REL" are clearly the same facility but are not currently recognized as such. Some of this work may require specific subject knowledge (e.g. should "MARCHY RMHU" and "MARCY RHMU/OSOTP" be considered the same?). Cleaning up the column headers is more tedious but easier, and perhaps could be done automatically.
