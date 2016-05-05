from __future__ import division, print_function
from urllib2 import urlopen 
from bs4 import BeautifulSoup
from sys import argv 
import pandas as pd
import numpy as np
import re, time
from geopy.geocoders import Nominatim, Bing

def parseCityLine(s, stateFullName = 'NA'):
    '''
    Uses regex to return city and zipCode from line of form: "City[,] SS[ ZZZZZ]"
    where SS is 2-digit state, Z is zip5, and things in brackets are optional.
    If stateFullName given, also accepts states of length stateFullName.
    Returns (city, [zipCode]) 
    '''
    return re.search('([\w\s\.]+)?,? (?:\D{2}|\D{%s})(?:\s+(\d{5}))?$' % len(stateFullName), s).groups()

    #return re.search('([\w\s]+)?,? \D{2}\s*(\d{5})?$', s).groups()

def parseStreet(s):
    s = re.sub('\s*#\d$', '', s).strip()
    return re.sub(',? ?(Ste|Suite|Rm|Room|Apt|Apartment|Bldg).+',"", s) #Remove Suites, Rooms, Apts.


def getStreet(streetList):
    '''Parses and returns first line that begins with a number.
    If doesn't exist, return all lines parsed and joined.'''
    for raw in streetList:
        s = raw.strip()
        if re.search('^([0-9#])', s):
            return parseStreet(s) 
    return ", ".join(map(parseStreet, streetList))
        


def getStreetCityLine(addressList):
    '''Designed initially for Illinois DMVs, to select:
    1. A cityLine (e.g. Chicago, IL 60613) as one ending with 5 digit zip.
    2. A parsed street that precedes the city line and begins with numbers.
    '''
    street = None

    for i, a in enumerate(addressList):
        streetSearch = re.search('^([0-9#])', a)
        citySearch = re.search(' \d{5}$', a)
        if streetSearch:
            street = parseStreet(a)
        elif citySearch:
            cityLine = a
            if not street:
                street = ", ".join(map(parseStreet, addressList[:i]))
            return(street, cityLine)


def getGeo(street, city, state, zipCode = ""):
    #Nominatim is fussier at street level than Bing.
    time.sleep(1)
    zipCode = zipCode if zipCode != None else ""
    with open('../keys/bingKey.txt') as f:
        bingKey = f.read()
    geoloc = Bing(bingKey)
    place = ("%s, %s, %s %s" % (street, city, state, zipCode)).strip()
    address = geoloc.geocode(query = place, timeout = 10)

    if not address: #If fails, abandon street and just go for the city's coords
        print("Bing maps can't find %s.  Trying again without street." % place)
        address = geoloc.geocode(query = "%s, %s %s" % (city, state, zipCode))

    #print (address.raw)
    #Return original zipcode if it exists, otherwise computes it.
    zipCode = zipCode if zipCode != "" else (address.raw['address']['postalCode'])
    try:    
        county = address.raw['address']['adminDistrict2'][:-1]+'unty'
    except:
        county = None

    return (address.latitude, address.longitude, zipCode, county)


def parsingPlay():
    '''Ended up not using yet'''
    yuck = ['3214 Auburn St., Rockford, IL 61101',
        '404 E. Stevenson Rd., Ottawa, IL 61350',
        "201 Danny's Dr., Ste. 6, Streator, IL 61364",
        'Sterling Bazaar Shopping Plaza, 3311 N. Sterling Ave. #12',
        'Twin Oaks Shopping Centre, 2001 Fifth St., Ste. 10, Silvis, IL 61282',
        'Sterling Bazaar Shopping Plaza, 3311 N. Sterling Ave. #12',
        'Southern Gardens Shopping Center, R.R. 5 Rte. 14 East, McLeansboro, IL 62859',
        'Lincoln Square Shopping Center, 901 W. Morton, Ste. 13, Jacksonville, IL 62650']

    def parseIt(x):
        rex = re.search('(?P<streetRaw>.+?)(?:, (?P<city>[\D ]+))?(?:, (?P<state>\D{2}) (?P<zipCode>\d{5}))?$',x)
        print (rex.group('streetRaw'))

    for y in yuck:
        parseIt(y)


def getDMVsIL():
    state = 'IL'
    soup = BeautifulSoup(urlopen('http://www.cyberdriveillinois.com/facilities/facilitylist.html'))
    agencyLinkList = [(x.a.text, x.a['href']) for x in soup.findAll("li")]

    geolocator = Nominatim(timeout = 60)
    ILlist = []

    for a in agencyLinkList:
        officeName = a[0]
        insides = BeautifulSoup(urlopen(a[1])).find('div',{'class':'appcell'}).div  
        addy = [i.strip() for i in insides.text.split("\n") if re.search('[A-z]', i)][:-1]
        (street, cityLine) = getStreetCityLine(addy)
        (city, zipCode) = parseCityLine(cityLine)
        #Look for latitude and longitued
        latlong = re.search('maps\?q=(?P<latitude>[-\d\.]+), (?P<longitude>[-\d\.]+)$', insides.a['href'])
        (latitude, longitude) = (np.nan, np.nan) if not latlong else latlong.groups()
        county = geolocator.reverse((latitude, longitude)).raw['address']['county']
        time.sleep(1)
        print (officeName, street, city, zipCode, county, state, latitude, longitude)
        ILlist.append([officeName, street, city, zipCode, county, state, latitude, longitude])

    df = pd.DataFrame(ILlist, columns = defaultColumns)
    return df

def getDMVsIN():
    state = 'IN'
    urlIN = 'http://www.in.gov/bmv/'
    soupIN = BeautifulSoup(urlopen(urlIN+'2337.htm')) 

    countyUrlList = [] #To be filled with (county names, url ends)
    for s in soupIN.find("form", {"name":"form1"}).findAll('option'):
        countyUrlList.append((s.text, s.get('value')))

    officeList = [] #To be filled with (county name, sentence describing BMV location.)
    for c in countyUrlList:
        county = c[0]
        soupC = BeautifulSoup(urlopen(urlIN+c[1])).find("div", {'id': 'col2content'})
        for office in soupC.findAll('p')[1:]:
            sen = re.sub('((,)? offers.*|.Contact.*|.)$','',office.text) #Take off terminus
            sen = re.search(r'The (.+) [lL]icense [Bb]ranch( is)? at (.*)', sen)

            if sen:
                #print(sen.group(1,3))
                officeName = sen.group(1)
                street = re.sub('(,|\xa0).*','', sen.group(3))
                rex = r' (- .*|AAA|North|South|East|West)$' #Remove these to get city name
                city = 'Indianapolis' if county == 'Marion' else re.sub(rex, '', officeName)
                (latitude, longitude, zipCode, _) = getGeo(street, city, state, "")
                officeList.append((officeName, street, city, zipCode, county+' County', state, latitude, longitude))

    df = pd.DataFrame(officeList, columns = defaultColumns)
    return df
    #df.to_csv('data/indianaDMVs.csv', encoding = 'utf-8')


def getDMVsOH():
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
    state = 'OH'
    stateList = []
    for countyItem in counties:
        (name, linkend) = countyItem
        county_soup = BeautifulSoup(urlopen(rootlink + linkend))
        for row in county_soup.table.findAll("tr")[1:]:
            addy = row.p.text.split('\r\n')
            cityZip = re.sub('\s?\(.*\)', '', addy[-2]).strip() #Remove things in parentheses.
            street = parseStreet(addy[1])
            (city, zipCode) = parseCityLine(cityZip, 'Ohio')

            try:
                (latitude, longitude, zipCode, _) = getGeo(street, city, state, zipCode)
                stateList.append([addy[0], street, city, zipCode, countyItem[0]+' County', state, latitude, longitude])
            except:
                print ("Failed for: ",[addy[0], street, city, zipCode, countyItem[0], state])

            
    df = pd.DataFrame(stateList, columns = defaultColumns)

    return df



def convertALdays(df):
    '''Alabama DL offices have non-standard opening hours.
    Need to convert so an office open once a month, or once a week is correct fraction
    of a M-F office (whose ratio would be 1).'''
    
    #First determine what fraction of a month is one day per month?
    #there are on average (5/7)*(365/12) =21.73 work days in a month:

    wpm = (5/7)*(365/12) #Workdays Per Month

    mwp = round(1/wpm,3) #inverse for Month fraction Per Workday

    #Dictionary to convert days open column to correct ratio
    daysConvert = {'M,Tu,W,Th,F':1, 'W':1/5, 'W,Th':2/5, '2nd Th':mwp, u'3rd Th':mwp, \
                   u'2nd M':mwp, u'1st Tu':mwp, u'Tu,W,Th':3/5, u'3rd W':mwp,\
                   u'Th,F':2/5, u'2nd W':mwp, u'Tu,W':2/5, u'M,Tu,Th,F':4/5,\
                   u'M, Tu, W':3/5, u'M,Tu':2/5, u'W, 2nd Tu':(0.2+mwp), u'1st W':mwp,\
                   u'2nd F':mwp, u'3rd Tu':mwp, u'1st T':mwp, u'M, Tu, W, Th, F': 1,\
                   u'2nd Th of month':mwp, u'4th Tu':mwp, u'3rd Tu & W':mwp,\
                   u'closed':0, u'T':1/5}
    
    dayratio = df.days.map(daysConvert)
    
    #Webs site has some extra warnings, inconsistencies that need to be addressed.
    dayratio[df.zipCode == 36507] = mwp
    dayratio[df.zipCode == 36518] = 0
    dayratio[df.zipCode == 36102] = 0
    
    return dayratio


def getDMVsAL():
    #Scrape the AL drivers license page
    state = 'AL'
    linkAL = 'http://dps.alabama.gov/home/DriverLicensePages/wfDLOffices.aspx'
    soupAL = BeautifulSoup(urlopen(linkAL))
    rex = re.compile(r'cplhMainContent_rptResults_lbl(Address|County|City|DaysOpen|ZipCode)_\d{1,2}')
    pageList = soupAL.findAll('span', {'id':rex})

    dmvList = []

    for i in range(0,len(pageList),5): 
        county = " ".join(map(str.capitalize, str(pageList[i].text).split()))
        #street = ", ".join(map(lambda x: x.strip(), pageList[i+1].contents[::2]))
        street = getStreet(pageList[i+1].contents[::2])
        city = pageList[i+2].text
        zipCode = int(pageList[i+3].text)
        days = pageList[i+4].text
        print(street+", "+city+", ", state, zipCode)
        (latitude, longitude, _, _) = getGeo(street, city, state, zipCode)
        dmvList.append((city, street, city, zipCode, county, state, latitude, longitude, days))
           
    df = pd.DataFrame(dmvList, columns = defaultColumns+['days'])

    df.replace("Dekalb County", "DeKalb County", inplace = True)
    df['open'] = convertALdays(df)
    
    return df.drop('days', axis = 1)



def getDMVsGA():
    state = 'GA'
    dmvList = []

    soup = BeautifulSoup(urlopen('http://www.dds.ga.gov/locations/locationlist.aspx'))
    for center in soup.tbody.find_all('tr'):
        (officeName, streetRaw, city, zipCode, county) = \
            [c.text.strip() for c in center.find_all('td')]
        street = parseStreet(streetRaw)
        (latitude, longitude, _, _) = getGeo(street, city, state, zipCode)
        dmvList.append([officeName, street, city, zipCode, county+' County', state, latitude, longitude])
        #print(officeName, street, city, zipCode, county, state, latitude, longitude)
    df = pd.DataFrame(dmvList, columns=defaultColumns)

    return df


def getDMVsTN():
    tnStarter = 'https://www.tn.gov/'
    state = 'TN'

    soup = BeautifulSoup(urlopen(tnStarter + 'safety/article/dllocationserv')).dl

    linkList = [(re.search('^(\w+ County)', li.a.text).group(1), li.a['href']) 
                for ul in soup.find_all('ul')[:2] for li in ul.find_all('li')]

    dmvList = []

    for link in linkList:
        county = link[0]
        soup1 = BeautifulSoup(urlopen(tnStarter + link[1])).find('div', {'id':'main'})
        soup2 = soup1.p.next_sibling.next_sibling.text.replace(u'\xa0', u' ').strip().split('\n')
        print(soup2)
        street = soup2[-2]
        (city, zipCode) = parseCityLine(soup2[-1]) #Separate City & Zip
        (latitude, longitude, zipCode, _) = getGeo(street, city, state, zipCode)
        #print((street, city, zipCode, county, 'TN', latitude, longitude))
        dmvList.append([city, street, city, zipCode, county, 'TN', latitude, longitude])

    df = pd.DataFrame(dmvList, columns = defaultColumns)
    return df
          

def getDMVsKY():
    state = 'KY'
    agencyList = []
    kyLink = 'http://drive.ky.gov/driver-licensing/Pages/License-Issuance-Locations.aspx'
    soup = BeautifulSoup(urlopen(kyLink)).tbody.findAll('tr')

    for s in soup:
        raw = s.findAll('td')
        county  = raw[0].text+' County'
        addressList = [g.string for g in raw[2] if (g.string not in [None, '\n', u'\xa0'])]
        (street, cityLine) = getStreetCityLine(addressList)
        (city, zipCode) = parseCityLine(cityLine)
        (latitude, longitude, _, _) = getGeo(street, city, state, zipCode)
        agencyList.append([county+' - '+city, street, city, zipCode, county, state, latitude, longitude])

    df = pd.DataFrame(agencyList, columns = defaultColumns)

    return df


def getDmv(state, save = True):
    #Make or load the merged database, as needed.
    fileLink = 'data/dmv'+state+'.csv'

    print("Looking for data on state: ", state)

    try:
        df = pd.read_csv(fileLink)
    except:
        if state == 'OH':
            df = getDMVsOH()
        elif state == 'IN':
            df = getDMVsIN()
        elif state == 'IL':
            df = getDMVsIL()

        elif state == 'AL':
            df = getDMVsAL()
        elif state == 'GA':
            df = getDMVsGA()
        elif state == 'TN':
            df = getDMVsTN()

        elif state == 'KY':
            df = getDMVsKY()

        if save == True:
            df.to_csv(fileLink, encoding = 'utf-8')

    print('\a') #Beep
    return df
    

defaultColumns = ['officeName','street','city', 'zipCode', 'county', 'state', 'latitude', 'longitude']


if __name__ == "__main__":
    if len(argv) > 2 and str(argv[2]).lower() == 'false':
        getDmv(argv[1], False) #False means don't save the file.
    else:
        getDmv(argv[1])
