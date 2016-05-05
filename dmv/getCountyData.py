from __future__ import division, print_function
import numpy as numpy
import pandas as pd
import os.path


def generateCountyDF(area_column):
	'''
	Not using this any more!  STCOU coding made it unneccessary.

	Returns df of counties and states (2 char abbrevs) when given
	a column of counties (and independent cities) from the US census. 
	Divide areas from counties like 'Alameda, CA' into separate 
	county and state columns.
	Fix downstream merging issue where 4 independent cities in VA 
	(e.g. 'Richmond, VA') have same name as a county they are not in.
	'''
	csList = []
	for c in area_column:
		cs = c.split(", ")
		if len(cs) == 1:
			if c == 'District of Columbia':
				csList.append(['Washington', 'DC'])
			else:
				csList.append([np.nan, np.nan])
		else:
			if cs in csList:
				csList.append([cs[0]+' City', cs[1]])
			else:
				csList.append(cs)
	return pd.DataFrame(countyStateList, columns = ['county', 'state'])   

def countyAreaFromXls():
	'''
	Returns geograph(land area) data for all US counties from XLS file on census website.
	Works out state and county codes from STCOU, a 5 digit number where first 2 digits 
	are for state, and last 3 are for county.
	
	Used census XLS file because not remotely obvious how to get geographic data from API.  
	Presumably county sizes don't change much, so this is ok.
	'''
	landURL = 'http://www2.census.gov/prod2/statcomp/usac/excel/LND01.xls'	
	df = pd.read_excel(landURL)[['STCOU','LND110210D', 'Areaname']]
	df.rename(columns = {'LND110210D': 'area'}, inplace = True)
	df['stateCode'] = df.STCOU//1000
	df['countyCode'] = df.STCOU%1000
	df =  df[df.countyCode != 0].reset_index(drop = True)
	return df.drop('STCOU', axis = 1)


def acquireCensus(urlend, colNames):
	'''
	Acquires and formats data from US Census API, returning pandas dataframe.
	'''
	df = pd.read_json('http://api.census.gov/data/'+urlend)
	colDict = {}
	for i in range(len(colNames)):
		colDict[i] = colNames[i]
	df = df.rename(columns = colDict).drop([0])
	df['stateCode'] = df.stateCode.astype(int)
	if 'countyCode' in df: df['countyCode'] = df.countyCode.astype(int)
	df = df[df.stateCode != 72] #Take out Puerto Rico for now
	return df.reset_index(drop = True)


def combineCensusData(filename = 'data/mainCensus.csv', makeNewFile = False):
	'''
	Returns dataframe containing county-level population, income, diversity, poverty,
	and land area from US Census.

	Takes inputs of filename (where to store a local csv).  If CSV already exists,
	returns existing CSV unless makeNewFile variable is changed to True.
	'''

	if makeNewFile or not os.path.isfile(filename):
		dfState = acquireCensus('2010/sf1?get=NAME&for=state:*', ['state', 'stateCode'])
		dfCounty = acquireCensus('2010/sf1?get=NAME&for=county:*&in=state:*', ['county', 'stateCode', 'countyCode'])

		#DP03_0119PE: PERCENTAGE OF FAMILIES AND PEOPLE WHOSE INCOME IN THE PAST 12 MONTHS IS BELOW THE POVERTY LEVEL!!All families
		#DP03_0088E: INCOME AND BENEFITS (IN 2013 INFLATION-ADJUSTED DOLLARS)!!Families!!Per capita income (dollars)
		dfIncome = acquireCensus('2013/acs5/profile?get=DP03_0088E&DP03_0119PE&for=county:*', 
									 ['perCapitaIncome', 'povertyPercent', 'stateCode', 'countyCode'])
		dfPopulation = acquireCensus('2010/sf1?get=P0010001&P0050003&for=county:*&in=state:*', 
									 ['population', 'nonHispanicWhite', 'stateCode', 'countyCode'])

		print( len(dfCounty), len(dfIncome), len(dfPopulation))

		df = dfCounty.merge(dfState, on = 'stateCode')[['stateCode', 'countyCode', 'county', 'state']]
		df = df.merge(dfIncome, on = ['stateCode', 'countyCode']).merge(dfPopulation, on = ['stateCode', 'countyCode'])
		dfGeog = countyAreaFromXls()
		df = df.merge(dfGeog, on = ['stateCode', 'countyCode'])
		df.to_csv(filename, encoding = 'utf-8')	
	else:
		df = pd.read_csv(filename)

	return df

if __name__ == '__main__':
	combineCensusData()