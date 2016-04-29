#Written for Python 2
from __future__ import division, print_function
from urllib2 import urlopen 
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from sklearn import linear_model
#from sklearn.cross_validation import train_test_split
import matplotlib.pyplot as plt

def dmvOhioList():
    #Make list of pages for each county
    linkOH = 'http://www.bmv.ohio.gov/locations.aspx'
    html = urlopen(linkOH)
    soup_main = BeautifulSoup(html)
    list_raw = soup_main.find("div", { "class" : "county-list" })
    #List of county names & url termini (ultimately didn't need as dataframe)
    counties = [[a.text[5:],a.get("href")] for a in list_raw.findAll("a")]
    #county_df = pd.DataFrame(counties, columns = ['name', 'link'])

    #Scrape each county page for DMV office information and return statewide list
    rootlink = 'http://www.bmv.ohio.gov/'
    statelist = []
    for county in counties:
        (name, linkend) = county
        county_soup = BeautifulSoup(urlopen(rootlink + linkend))
        for row in county_soup.table.findAll("tr")[1:]:
             statelist.append([name] + row.p.text.split("\r\n",1) + [row.a.get('href')])
    len(statelist)
    df = pd.DataFrame(statelist, columns = ['county', 'agency', 'address', 'maplink'])
    return df

def cleanNacoData(link):
    #Downloaded county population and size data from http://explorer.naco.org/
    #Prep that for merging with scraped DMV data
    df = pd.read_csv(link)
    df.drop(['BOARD SIZE', 'FOUNDED'], axis = 1, inplace = True)
    df.columns = ['county','population 2013','sqmi','countySeat']
    df.county = df.county.map(lambda x: x.rsplit(" ",1)[0])
    return df

def getDmvOH():
    #Make or load the merged database, as needed.
    file_link = 'data/mergedOHdata.csv'
    try:
        df = pd.read_csv(file_link)
    except:
        dmv = dmvOhioList()
        naco = cleanNacoData('data/nacoOH.csv')
        df = pd.merge(naco, dmv, on = 'county')
        df.to_csv(file_link)
    return df

def plotOH():
    #Load Ohio data, fit with linear regression, and plot along with regression line.
    dfOH = getDmvOH()
    X = dfOH.groupby('county')['population 2013'].median()#.values
    y = dfOH.groupby('county').agency.count().values
    X = np.array(X).reshape((len(X), 1))

    linreg = linear_model.LinearRegression()
    linreg.fit(X, y)
    plt.clf()
    plt.scatter(X, y)
    plt.xlim((0,1400000))
    plt.ylim((0,20))
    plt.xlabel("Population of County")
    plt.ylabel("DMV agency count")
    plt.title("Ohio")
    plt.plot(X, linreg.predict(X), color='blue', linewidth=1)
    plt.savefig('opp_app/static/OH1.png')
    plt.close()
    
def convertALdays(df):
    #Alabama DL offices have non-standard opening hours.
    #Need to convert so an office open once a month, or once a week is correct fraction
    #of a M-F office (whose ratio would be 1).
    
    #First determin what fraction of a month is one day per month?
    #there are on average (5/7)*(365/12) =21.73 work days in a month:
    workdays_per_month = round((5/7)*(365/12))
    mfxn = round(1/workdays_per_month,3) #mfxn is month fraction in a day
    
    #Dictionary to convert days open column to correct ratio
    daysConvert = {'M,Tu,W,Th,F':1, 'W':1/5, 'W,Th':2/5, '2nd Th':mfxn, u'3rd Th':mfxn, \
                   u'2nd M':mfxn, u'1st Tu':mfxn, u'Tu,W,Th':3/5, u'3rd W':mfxn,\
                   u'Th,F':2/5, u'2nd W':mfxn, u'Tu,W':2/5, u'M,Tu,Th,F':4/5,\
                   u'M, Tu, W':3/5, u'M,Tu':2/5, u'W, 2nd Tu':(0.2+mfxn), u'1st W':mfxn,\
                   u'2nd F':mfxn, u'3rd Tu':mfxn, u'1st T':mfxn, u'M, Tu, W, Th, F': 1,\
                   u'2nd Th of month':mfxn, u'4th Tu':mfxn, u'3rd Tu & W':mfxn,\
                   u'closed':0, u'T':1/5}
    
    dayratio = df.days.map(daysConvert)
    
    #Webs site has some extra warnings, inconsistencies that need to be addressed.
    dayratio[df.zipcode == 36507] = mfxn
    dayratio[df.zipcode == 36518] = 0
    dayratio[df.zipcode == 36102] = 0
    
    return dayratio


def dmvALlist():
    #Scrape the AL drivers license page
    linkAL = 'http://dps.alabama.gov/home/DriverLicensePages/wfDLOffices.aspx'
    htmAL = urlopen(linkAL)
    soupAL = BeautifulSoup(htmAL)
    tables = soupAL.find(id="tblMainContent").tr.findAll('table')[40]
    countyDict = {}
    openDict = {}
    zipDict = {}

    for s in tables.findAll('span'):
        if s.get('id')[:37] == 'cplhMainContent_rptResults_lblCounty_':
            idnum = int(s.get('id')[37:])
            countyDict[idnum] = (s.text.rsplit(" ",1)[0]).capitalize()
        if s.get('id')[:38] == 'cplhMainContent_rptResults_lblZipCode_':
            idnum = int(s.get('id')[38:])
            zipDict[idnum] = int(s.text)
        if s.get('id')[:39] == 'cplhMainContent_rptResults_lblDaysOpen_':
            idnum = int(s.get('id')[39:])
            openDict[idnum] = s.text
 
    alDMV = pd.DataFrame([countyDict, zipDict, openDict]).transpose()
    alDMV.columns = ["county", "zipcode", "days"]
    alDMV.replace("Dekalb", "DeKalb", inplace = True)
    alDMV.replace("St. clair", "St. Clair", inplace = True)
    alDMV['dayratio'] = convertALdays(alDMV)
    
    return alDMV

def getALdmv():
    #Load saved, or produce new merged AL dataframe
    
    file_link = 'data/mergedALdata.csv'
    try:
        df = pd.read_csv(file_link)
    except:
        nacoAL = cleanNacoData('data/nacoAL.csv')
        dmvAL = dmvALlist()
        df= pd.merge(nacoAL, dmvAL, on = 'county', how = 'outer')
        df.dayratio.replace(np.nan, 0, inplace = True)
        df.to_csv(file_link)
    return df

def plotAL():
    dfAL = getALdmv()
    X = dfAL.groupby('county')['population 2013'].median()
    y = dfAL.groupby('county').dayratio.sum()
    plt.clf()
    plt.scatter(X.values, y.values)
    plt.ylim((0,2.50))
    plt.xlim((0,700000))
    plt.xlabel("Population of County")
    plt.ylabel("DMV agency count")
    plt.title("Alabama")

    Xre = np.array(X).reshape((len(X), 1))
    linreg = linear_model.LinearRegression()
    linreg.fit(Xre,y)

    plt.plot(Xre, linreg.predict(Xre), color='blue', linewidth=1)
    plt.savefig('opp_app/static/AL1.png')
    plt.close()


if __name__ == "__main__":
    plotOH()
    plotAL() 
