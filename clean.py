#read from csvs folder and dump to cleancsvs folder

import pandas
import os
import sys
import numpy

CSV_DIR = 'csvs'
CLEAN_CSV_DIR = 'cleancsvs'
VERBOSE = False
DEBUG = False

if not os.path.exists(CSV_DIR):
    print('No directory', CSV_DIR, 'found')
    sys.exit()
    
csvnames = [name for name in os.listdir(CSV_DIR) if name.endswith('.csv')]
csvnames.sort()

#2018-12 forms are messed up in a novel way: tables can be vertically across pages rather than horizontally
csvnames = [csvname for csvname in csvnames if not csvname.startswith('IPR2018-12')]


tabletypedict = {
    '1': 'Age',
    '2': 'Ethnicity',
    '3A': 'Crime',
    '3B': 'Crime group',
    '4': 'Min sentence',
    '5': 'Max sentence',
    '6': 'County of commitment',
    '7': 'Religion',
    '8': 'Marital status',
    '9': 'Education',
    '10': 'Length of stay',
    '11': 'Gender',
    '12': 'Status',
    '13': 'Latest admission type'
}

#these are the ones we will clean up - columns all of same form
tabletypeindices = ['1', '2', '3A', '3B', '4', '5', '6', '7', '8', '9', '10', '13']

#unique headers that help us identify which table is which. for multi-page tables we need a bunch of possibilities
keywords = {
    '1': ['18-20'],
    '2': ['WHITE'],
    '3A': ['MURDER', 'ROBBERY', 'ASSAULT', 'BURGLARY', 'KIDNAP', 'DRIVE', 'WEAPONS'],
    '3B': ['VIOLENT'],
    '4': ['LT 18'],
    '5': ['36 OR LESS'],
    '6': ['KINGS', 'BRONX', 'ERIE', 'CAYUGA', 'ESSEX', 'GREENE', 'ORANGE', 'PUTNAM', 'TIOGA', 'YATES'],
    '7': ['CATHOLIC'],
    '8': ['MARRIED'],
    '9': ['GRADE'],
    '10': ['0-2'],
    '11': ['MALE'],
    '12': ['INMATE', 'RELEASEE'],
    '13': ['COURT']
}

#these are the dates whose Table 10s are weird and row consolidation needs to be resolved downward
rowconsolidationproblemdates = ['IPR2015-06', 'IPR2016-08', 'IPR2016-10', 'IPR2018-06', 'IPR2018-10', 'IPR2018-11', 'IPR2019-02', 'IPR2020-03', 'IPR2020-05']

#these can be types of facilities
facilitytypes = ['MAXIMUM SECURITY', 'MEDIUM SECURITY', 'MINIMUM SECURITY', 'MINIMUM WORK RELEASE', 'FEMALE FACILITY', 'ADOLESCENT OFFENDER FACILITIES', 'PAROLE PROGRAM FACILITIES', 'PROGRAM FACILITIES'] 
#in above need to put 'parole program facilities' first so it is greedy checked first

#these special row headers cannot be types of facility
specialheaders = ['CORRECTIONS TOTAL', 'SUBTOTAL', 'COMMNT SUPV TOTAL', 'COMMUNITY SUPRV TOTAL', 'GRAND TOTAL', 'CORRECTIO NS TOTAL', 'CORRECTION S TOTAL']

#headers for multiple columns that we discard
superheaders = ['NEW YORK CITY', 'SUBURBAN N.Y.', 'UPSTATE URBAN', 'UPSTATE OTHER', 'UPSTATE ...', 'NO CODE', 'LATEST ADMISSION TYPE'] 

#we will check up to this number of rows for a facility type or special header
MAXHEADERROWS = 4



#checks whether rows of dataframe df are complementary; i.e. if for for each column there is at most one non-Nan, 'nan', or empty string entry
def complementary(df):
    return not (df.replace({'':numpy.NaN}).replace({'nan':numpy.NaN}).isna().replace({True:0, False:1}).sum() > 1).any()

#takes in series, string and checks whether the string is spread out over the series, in order. words can skip at most one row. returns (False, None) if this does not occur and (True, ser) if it does, where ser is the series with string removed
def headercheck(ser, string):
    count = 0
    if string.split()[0] not in str(ser[ser.index[0]]):
        return (False, None)
    for word in string.split():
        if word in ser[ser.index[count]]:
            ser[ser.index[count]] = str(ser[ser.index[count]]).replace(word, '', 1).strip()
        elif count + 1 < len(ser.index) and word in str(ser[ser.index[count + 1]]):
            count = count + 1
            ser[ser.index[count]] = str(ser[ser.index[count]]).replace(word, '', 1).strip()
        elif count + 2 < len(ser.index) and word in str(ser[ser.index[count + 2]]):
            count = count + 2
            ser[ser.index[count]] = str(ser[ser.index[count]]).replace(word, '', 1).strip()
        else:
            return (False, None)        
    if count == len(ser) - 1:
        return (True, ser)
    else:
        return (False, None)

#takes in series and list of strings and applies headercheck to each string. returns (False, None, None) if none work and (True, ser, string) when it finds string that works, where ser is the series with string removed
def listheadercheck(ser, lst):
    for string in lst:
        (flag, s) = headercheck(ser.copy(), string)
        if flag:
            return (True, s, string)
    return (False, None, None)

#takes series of strings and joints, but removes spaces and hyphens as appropriate
def smartjoin(ser):
    string = ''
    for (ind,val) in ser.items():
        val = val.strip()
        string = string + ' ' + val
    return string.replace('  -','').replace(' -','').replace('-  ','').replace('- ','').replace('  ',' ').strip()

#tests whether a series is mostly nans
def mostlynans(ser):
    return ser.isna().replace({True:1, False:-1}).sum() > 0

#tests whether a series 1) has at least one %, and 2) all entries have either %, 0, or NaN
def ispercent(ser):
    ser = ser.astype(str)
    hasonepercent = False
    for (index, value) in ser.items():
        if '%' in value:
            hasonepercent = True
        if value != '0' and value != 'nan' and '%' not in value:
            return False
    if hasonepercent:
        return True
    else:
        return False
    
overwrite = False
while True:
    yn = input('Overwrite? y/n')
    if yn == 'y':
        overwrite = True
        break
    elif yn == 'n':
        overwrite = False
        break
        
if not os.path.exists(CLEAN_CSV_DIR):
    os.makedirs(CLEAN_CSV_DIR)

problems = [] #list of file names that we fail to read
count = 0
prevtabletype = ''
for name in csvnames:
    if not overwrite and os.path.isfile(os.path.join(CLEAN_CSV_DIR, name)):
        print('Clean file already exists for', name)
        continue
    
    count = count + 1
    if VERBOSE:
        print('Attempting to clean', name)
    frame = pandas.read_csv(os.path.join(CSV_DIR, name))
    
    if DEBUG:
        print(frame.iloc[:,:10].to_string())
        
    #identify what kind of table we have
    firstrowstring = ''.join([str(n) for n in frame.iloc[0].tolist()])
    initstring = firstrowstring.split('.')[0]
    index = initstring.find('TABLE')
    if index != -1:
        tabletype = initstring[index + 6:]
        try:
            tabletypestr = tabletypedict[tabletype]
            frame = frame.drop([0]).reset_index(drop = True) #0th row contains no useful info except table type
            if VERBOSE:
                print('  Table type is', tabletype, tabletypestr)
        except: #this should not happen
            print('  ERROR: Table type not recognized in', name)
            problems.append(name)
            continue
    else: #sometimes header doesn't get picked up, so we try to use keywords
        chunk = frame.iloc[:5,:].copy()
        found = False
        for key in keywords:
            if found:
                break
            for string in keywords[key]:
                if found:
                    break
                mask = chunk.applymap(lambda x: string in x if isinstance(x,str) else False)
                if mask.any().any():
                    found = True
                    tabletype = key
                    tabletypestr = tabletypedict[tabletype]
                    if VERBOSE:
                        print('  Table type is', tabletype, tabletypedict[tabletype])
                    break
        if not found: #if all else fails, assign previous table type
            tabletype = prevtabletype
            tabletypestr = tabletypedict[tabletype]
            print('  WARNING: Table type assigned to previous table type', tabletype, tabletypestr, 'by default in', name)      
    prevtabletype = tabletype
    
    #if it isn't one of types in tabletypesindices, do not proceed
    if tabletype not in tabletypeindices:
        print('  Table type not in list; aborting cleaning for', name)
        problems.append(name)
        continue
            
    #if there is no GRAND [TOTAL] row, do not proceed - camelot did not work properly
    if not frame.iloc[:,0].str.contains('GRAND').replace(numpy.NaN, False).any():
        print('  Camelot did not read entire table; aborting cleaning for', name)
        problems.append(name)
        continue
                
    #attempt to find 'SECURITY LEVEL AND FACILITY' in first column to figure out where column headers end
    columnheaderend = None
    slffound = False
    for beginrow in range(4):
        for i in range(1, MAXHEADERROWS):
            endrow = beginrow + i
            (flag, ser) = headercheck(frame.iloc[beginrow:endrow,0].copy(),'SECURITY LEVEL AND FACILITY')
            if flag: #found it
                columnheaderend = endrow
                slffound = True
    #if that doesn't work, look just for 'SECURITY LEVEL'
    if not slffound:
        if VERBOSE:
            print('  Could not find phrase \'SECURITY LEVEL AND [HOUSING] FACILITY\' in usual place; looking for abbreviated version')
        for beginrow in range(2):
            for i in range(1, MAXHEADERROWS):
                endrow = beginrow + i
                (flag, ser) = headercheck(frame.iloc[beginrow:endrow,0].copy(),'SECURITY LEVEL')
                if flag: #found it
                    if VERBOSE:
                        print('  Abbreviated version found')
                    columnheaderend = endrow
                    slffound = True    
    if not slffound:
        print('ERROR: could not find end of column headers. Aborting cleaning for', name)
        problems.append(name)
        continue
    
    if VERBOSE:
        print('  Found column header end:', columnheaderend)
        
    if DEBUG:
        print(frame.to_string())
        
                        
    #look in first row for column superheaders and remove
    numcols = len(frame.columns)
    for col in range(numcols):
        for superheader in superheaders:
            if superheader == str(frame.iloc[0,col]).strip():
                frame.iloc[0,col] = numpy.NaN
                
    #detect whether facility attributes are in their own column or not. if the 0th column is mostly nans, they are
    facattcol = mostlynans(frame.iloc[:,0].copy())
    #if facattcol, consolidate first two columns. this isn't the most elegant thing to do, perhaps, but it reduces us to the 'not facattcol' case
    if facattcol:
        if VERBOSE:
            print('  Seperate header column detected; consolidating first two columns')
        frame.iloc[:,0] = (frame.iloc[:,0].astype(str).replace('nan','') + ' ' + frame.iloc[:,1].astype(str).replace('nan','')).str.strip()    
        frame.drop(frame.columns[1], axis = 1, inplace = True)
                    
    #try to combine columns if they are complementary. proceed in order and greedily
    newframe = pandas.DataFrame()
    begincol = 0
    numcols = len(frame.columns)
    count = 0
    while begincol < numcols:
        endcol = begincol + 2     
        while endcol <= numcols and complementary(frame.iloc[:, begincol:endcol].T): #current chunk is still complementary
            endcol = endcol + 1
        endcol = endcol - 1
        #consolidate and assign as new column
        consolidated = frame.iloc[:, begincol:endcol].T.fillna(method = 'bfill').iloc[0,:]
        newframe[count] = consolidated
        begincol = endcol
        count = count + 1
    frame = newframe
    if VERBOSE:
        print('  Complementary columns consolidated for', name)   
        
    #now join all rows before columnheaderend
    headerchunk = frame.iloc[:columnheaderend,:].copy()
    headerchunk = headerchunk.replace({numpy.NaN:''}).astype(str)
    row = headerchunk.agg(smartjoin).to_frame().T    
    everythingelse = frame.iloc[columnheaderend:,:].copy()
    frame = pandas.concat([row, everythingelse])
    if VERBOSE:
        print('  Column headers consolidated')
        
    #assign first row as column headers and drop first row
    frame.columns = frame.iloc[0].rename(None)
    frame = frame.drop([0]).reset_index(drop = True)
            
    #rename first column label
    frame.rename({frame.columns[0]:'Facility'}, axis = 1, inplace = True)
        
    newframe = pandas.DataFrame()
    
    if DEBUG:
        print(frame.to_string())
    
    #now we look for facility attributes and special headers and reassign them
    #we add an additional column to support facility attributes
    numrows = len(frame.index)
    beginrow = 0
    currtype = ''
    while beginrow < numrows:
        for i in range(MAXHEADERROWS, 0, -1): #start with longest possible consolidation
            specialheader = ''
            endrow = beginrow + i
            chunk = frame.iloc[beginrow:endrow, :].copy()
            (flag, ser, string) = listheadercheck(chunk.iloc[:,0].copy(), facilitytypes)
            if string == currtype: #don't want MAXIMUM SECURITY RRU, etc. to count as header
                break
            elif flag: #found a facility attribute
                currtype = string
                chunk.iloc[:,0] = ser.astype('string')
                break
            else:
                (flag, ser, string) = listheadercheck(chunk.iloc[:,0].copy(), specialheaders)
                if flag: #found a special header
                    chunk.iloc[:,0] = ser.astype('string')
                    specialheader = string
                    break
        chunk.iloc[0,0] = specialheader + str(chunk.iloc[0,0]) #put special header back
        chunk['Facility type'] = pandas.Series(currtype, chunk.index)
        newframe = pandas.concat([newframe, chunk])
        beginrow = endrow
        
    frame = newframe
    
    if VERBOSE:
        print('  Facility types and special headers cleaned for', name)
    
    #special headers don't have facility types
    frame.loc[frame['Facility'].isin(specialheaders), frame.columns[-1]] = 'SPECIAL HEADER'
        
    #CHECK that everything has a facility type
    if frame['Facility type'].isna().any():
        print('  WARNING: facility types not assigned for all rows')
    elif VERBOSE:
        print('  Passed test: facility types assigned for all rows')
                
    #delete rows of percentages: we don't need them, and they shouldn't have a header at this point, so they can screw things up if we don't
    subframe = frame.iloc[:,1:-1]    
    indices = frame.index[subframe.apply(ispercent, axis = 1)]
    headers = frame.loc[indices, :].iloc[:,0]
    headers = headers.replace({'':numpy.NaN}).replace({'nan':numpy.NaN})
    if headers.isna().all():
        frame.drop(indices, inplace = True)
    else:
        print('  WARNING: found rows of percentages with nontrivial headers')
    frame.reset_index(drop = True)
    if VERBOSE:
        print('  Rows of percentages removed for', name)
                
    #remove last row if it just contains a page number OR footnote 'COLLEGE REPRESENTS...'
    lastrow = frame.tail(1).copy()
    lastrowsum = lastrow.replace({'nan':numpy.NaN, '':numpy.NaN}).isna().replace({True:0,False:1}).sum(1).iloc[0]
    if (lastrowsum == 2) and ('Page' in str(lastrow.iloc[0,-2]) or 'Page' in str(lastrow.iloc[0,-3]) or 'COLLEGE REPRESENTS' in str(lastrow.iloc[0,0])):
        frame.drop(lastrow.index, inplace = True)
        
    if DEBUG:
        print(frame.to_string())
                           
    #try to combine rows if they are complementary. again proceed in order and greedily.
    newframe = pandas.DataFrame()
    numrows = len(frame.index)
    beginrow = 0
    while beginrow < numrows:
        endrow = beginrow + 2
        while complementary(frame.iloc[beginrow:endrow, :-1]) and endrow <= numrows:
            endrow = endrow + 1
        chunk = frame.iloc[beginrow:endrow - 1, :].fillna(method = 'bfill').head(1) #this is a dataframe with one row
        newframe = pandas.concat([newframe, chunk])
        beginrow = endrow - 1        
    frame = newframe.reset_index(drop = True)
    if VERBOSE:
        print('  Complementary rows consolidated for', name)    
        
    if DEBUG:
        print(frame.to_string())
    
    #now any rows that are complementary except for the facility get resolved greedily, *UNLESS* we are in table 3A or 6, where there are often many missing rows. if we are in table 10 and one of the problem dates, reconcile anti-greedily/downwards (but only need to check two rows at a time)
    bad10flag = False
    for date in rowconsolidationproblemdates:
        if name.startswith(date):
            bad10flag = True
    if (tabletype != '3A' and tabletype != '6' and tabletype != '10') or (tabletype == '10' and not bad10flag):
        newframe = pandas.DataFrame()
        numrows = len(frame.index)
        beginrow = 0
        while beginrow < numrows:
            endrow = beginrow + 2
            while complementary(frame.iloc[beginrow:endrow, 1:-1]) and endrow <= numrows:
                endrow = endrow + 1
            chunk = frame.iloc[beginrow:endrow - 1, :].fillna(method = 'bfill').head(1)
            if endrow - beginrow > 2:
                facility = smartjoin(frame.iloc[beginrow:endrow - 1, 0])
                chunk['Facility'] = facility
            newframe = pandas.concat([newframe, chunk])
            beginrow = endrow - 1   
        if VERBOSE:
            print('  Further row consolidation completed for', name)
        frame = newframe.reset_index(drop = True)
    elif tabletype == '10' and bad10flag: #reconcile downwards
        row = 1
        while row < len(frame.index) - 1:
            if frame.iloc[row, 1:-1].isna().all():
                facility = smartjoin(frame.iloc[row:row+2,0])
                frame.iloc[row + 1,0] = facility
                frame.drop(row, inplace = True)
                frame = frame.reset_index(drop = True)
            row = row + 1        
                        
    if DEBUG:
        print(frame.to_string())
                             
    #Replaces any remaining NaNs with 0s
    frame = frame.fillna(0)
                
    #CHECK that everything that should be an int is one
    noavgframe = frame.iloc[:,1:-1].drop([x for x in frame.columns if 'AVERAG' in x], axis = 1)
    try:
        noavgframe = noavgframe.astype('int')
        if VERBOSE:
            print('  Passed test: expected integer entries are integers')
    except:
        print('WARNING:', name, 'contains unexpected non-integer entries')
                
    #CHECK column subtotals
    flag = True
    subtotalindexes = []
    for ftype in facilitytypes:
        smallframe = noavgframe[frame['Facility type'] == ftype]
        if smallframe.empty:
            continue
        subtotalindex = smallframe.index[-1] + 1
        subtotalindexes.append(subtotalindex)
        subtotalrow = noavgframe.iloc[subtotalindex,:]
        if not smallframe.sum().equals(subtotalrow):
            print('WARNING: subtotals for facility type', ftype, 'in', name, 'appear to be incorrect')
            flag = False
    if flag and VERBOSE:
        print('  Passed test: all column subtotals are correct')

    #now that they've been checked, remove them:
    frame.drop(subtotalindexes, inplace = True)
    noavgframe.drop(subtotalindexes, inplace = True)
    frame = frame.reset_index(drop = True)
    noavgframe = noavgframe.reset_index(drop = True)
        
    #CHECK corrections total
    totalrows = noavgframe[frame['Facility type'] == 'SPECIAL HEADER']
    index = totalrows.index[0]
    if totalrows.iloc[0,:].equals(noavgframe.iloc[:index,:].sum()):
        if VERBOSE:
            print('  Passed test: corrections totals are correct')
    else:
        print('WARNING: corrections totals for', name, 'appear to be incorrect')
        
    #remove corrections total row
    frame.drop(index, inplace = True)
    noavgframe.drop(index, inplace = True)
        
    #CHECK grand total
    grandtotalrow = noavgframe.iloc[-1,:]
    if grandtotalrow.equals(noavgframe.iloc[:-1].sum()):
        if VERBOSE:
            print('  Passed test: grand totals are correct')
    else:
        print('WARNING: grand totals for', name, 'appear to be incorrect')
        
    #remove grand total row
    frame.drop(frame.index[-1], inplace = True)
    
    #finally: starting in 2019 multi-page tables pick up next column of data somehow but have empty headers, so we delete
    columns = frame.columns
    if columns[-2] == '':
        if VERBOSE:
            print('  Caution: dropping column with null header that is expected to be duplicated in', name)
        frame.drop(columns[-2], axis = 1, inplace = True)
            
    #set multi-index rows. Two levels: facility type and facility
    frame.set_index(['Facility type', 'Facility'], inplace = True)    
    
    #set multi-index columns. Three levels: date, table type, then column label
    length = len(frame.columns)
    dates = [name[3:10]] * length
    types = [tabletype] * length
    multiindex = pandas.MultiIndex.from_tuples(list(zip(dates, types, frame.columns)), names = ['Date', 'Table', 'Column'])
    frame.columns = multiindex
    
    pathname = os.path.join(CLEAN_CSV_DIR, name)
    frame.to_csv(pathname)
    
    if DEBUG:
        print(frame.to_string())
    
        
    print(name, 'cleaned and written to', pathname)
    
print(problems)