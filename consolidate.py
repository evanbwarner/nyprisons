#reads in all csv files in cleancsvs directory and attempts to merge them and write to one big file data.csv

import pandas
import os

CLEAN_CSV_DIR = 'cleancsvs'

csvnames = [name for name in os.listdir(CLEAN_CSV_DIR) if name.endswith('.csv')]
csvnames.sort()

bigframe = pandas.DataFrame()

for name in csvnames:
    frame = pandas.read_csv(os.path.join(CLEAN_CSV_DIR, name), index_col = [0,1], header = [0,1,2])
    
    #before we concatenate, we have to disambiguate: e.g. page 2 of 2016-02 has two 'FIVE POINTS' for example (clearly one should be FIVE POINTS RMHU but I'll avoid making that judgment here)
    indexlist = frame.index.tolist()
    dup = frame.index.duplicated()
    for i in range(len(indexlist)):
        if dup[i]:
            print('WARNING: a facility name for', name, 'is duplicated')
            newstr = str(indexlist[i][1]) + ' (DUPLICATE)'
            newtuple = tuple([indexlist[i][0], newstr])
            indexlist[i] = newtuple
    newindex = pandas.MultiIndex.from_tuples(indexlist)
    frame.set_index(newindex, inplace = True)

    bigframe = pandas.concat([bigframe, frame], axis = 1)
    
bigframe.to_csv('data.csv')