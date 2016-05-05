from __future__ import division, print_function
import pandas as pd
import matplotlib.pyplot as plt

def fixCountyNames(countyList):
    '''Census has all Saint X as St. X and Dekalb as DeKalb.
    so fix these in the state DMV file.'''
    newList = []
    for county in countyList:
        if county.split()[-1] != 'County':
            county = county+' County'    
        csplit = county.split()
        if csplit[-1] != county:
            csplit
        if csplit[0] == 'Saint':
            county = ('St. '+" ".join(csplit[1:]))
        if county == 'Dekalb County':
            county = 'DeKalb County'
        newList.append(county)
    return newList


def dmvScatter(df, fileName = '../opp_app/static/7states.png'):
    colors  = ['b','g','r','c','m','y','k']
    plt.figure(figsize=(7, 10))
    plt.xlabel('longitude')
    plt.ylabel('latitude')
    plt.ylim(30, 43)
    plt.xlim(-92, -80)
    plt.title('DMV Locations in Seven States\n(Bet you can guess which ones.)')
    for i, state in enumerate(df.state.unique()):
        dfs = df[df.state == state]
        plt.scatter(dfs.longitude, dfs.latitude, color = colors[i])
    plt.savefig(fileName)


def main():
    dfDMV = pd.read_csv('data/allDMV.csv', index_col=0)
    #Some county names are not same as in census, so fix that.
    dfDMV['county'] = fixCountyNames(dfDMV.county.values)

    #AL had partial days (like once per month!)
    #But most places have full time offices, so set those to 1.
    dfDMV.open.fillna(value = 1, inplace = True) 

    #Read in census data, select for just the states we're worrying about now, and merge.
    dfCen = pd.read_csv('data/mainCensus.csv', index_col = 0)
    dfCen7 = dfCen[dfCen.state.isin([state for state in dfDMV.state.unique()])]
    df = pd.merge(dfDMV, dfCen7, on = ['state', 'county'], how = 'outer')
    if df.countyCode.isnull().max():
        raise Exception(
            ''' Not merging correctly. Check if some DMV counties don\'t match Census style. 
                See specifically these counties: \n%s''' % (df[df.countyCode.isnull()][['county', 'state']]))

    df.open.fillna(value = 0, inplace = True) #Counties with no office
    df['countyDMVCount'] = df.groupby(['state', 'county']).open.transform('sum')
    df.to_csv('data/dmvCensus7states.csv', encoding = 'utf-8')
    dmvScatter(df)

if __name__ == '__main__':
    main()

