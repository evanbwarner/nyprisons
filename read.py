#some examples of how to use the output of consolidate.py

import pandas
import os
import matplotlib.pyplot as plt

bigframe = pandas.read_csv('data.csv', index_col = [0,1], header = [0,1,2])
bigframe.sort_index(inplace = True) #this improves performance

#1) how many people committed from Kings County (Brooklyn) are incarcerated in Attica, over time?
series1 = bigframe.loc[(slice(None),'ATTICA'),(slice(None),'6','KINGS')].squeeze()
series1.index = series1.index.droplevel(2).droplevel(1)
series1.plot.line(title = 'People committed in Brooklyn and incarcerated at Attica', ylabel = 'Number of people')
plt.show()

#note that we're missing a fair amount of data! table 6 is hard to read

#2) let's normalize: how many people are in Attica period? use table 1, since it's easy to read
series2 = bigframe.loc[(slice(None),'ATTICA'),(slice(None),'1','TOTAL')].squeeze()
series2.index = series2.index.droplevel(2).droplevel(1)

#we've already dropped the non-relevant levels of the multiindexes, so we can just divide and plot
series3 = series1/series2
series3.plot.line(title = 'People incarcerated at Attica: proportion committed in Brooklyn', ylabel = 'Proportion of total')
plt.show()

#Gaps (NaNs) appear for some missing data, as one would expect

#3) among married prisoners, what proportions are in max/med/min security?
seriesmax = bigframe.loc[('MAXIMUM SECURITY',),(slice(None),'8','MARRIED')].sum().droplevel(2).droplevel(1)
seriesmed = bigframe.loc[('MEDIUM SECURITY',),(slice(None),'8','MARRIED')].sum().droplevel(2).droplevel(1)
seriesmin = bigframe.loc[('MINIMUM SECURITY',),(slice(None),'8','MARRIED')].sum().droplevel(2).droplevel(1)
seriestot = bigframe.loc[:,(slice(None),'8','MARRIED')].sum().droplevel(2).droplevel(1)
(seriesmax/seriestot).plot.line(label = 'Max. security')
(seriesmed/seriestot).plot.line(label = 'Med. security')
(seriesmin/seriestot).plot.line(label = 'Min. security')
plt.legend()
plt.ylabel('Proportion of total')
plt.title('Married prisoners: proportion in max/med/min security')
plt.show()

