from __future__ import division, print_function
import pandas as pd
import geopy, pickle, time, accessSQLdb, os.path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

#This file looks through the tweets of interest, evaluates if they have GPS 
#coordinates.  In order to save time (and not annoy the API hosts), make a dictionary
#of all gps->address look ups and pickle it.

def save_dict(locsDict, pkl_filename, final = True):
	#Pickle the dictionary.
	if not final:
		pkl_filename += 'INCOMPLETE'
	with open(pkl_filename, 'w') as f:
		pickle.dump(locsDict, f, pickle.HIGHEST_PROTOCOL)


def makeGeoDict(gps_set, geodict, gpsPklFilename):
	#Make the dictionary
	geolocator = Nominatim()

	for i, gps_tuple in enumerate(gps_set):
		#x is coordinate as tuple
		try:
			geodict[gps_tuple] = geolocator.reverse(str(gps_tuple)[1:-1]).address
			time.sleep(1)
			if ((i+1)%50 == 0):
				print("Checked %4d (%4.1f%%) so far." %((i+1),(100*(i+1)/len(gps_set))))
				save_dict(geodict, gpsPklFilename, final = False)

		except GeocoderTimedOut as e:
			print("Error: geocode failed on input #%d = %s with message %s."%(i, gps_tuple, e.message))
			print("Saving incomplete dictionary.")
			save_dict(geodict, gpsPklFilename, final = False)

	save_dict(geodict, gpsPklFilename)

	return geodict


def getGeoDict(sqlDBfile, csv_name, gpsPklFilename):
	#If final dictionary exists, return that.
	if os.path.exists(gpsPklFilename):
		with open(gpsPklFilename, 'r') as f:
			geodict = pickle.load(f)
		print ("You have a dictionary file with %d entries." % len(geodict))
		return(geodict)

	else:
		geodict = {}
		df = accessSQLdb.getFromSql(sqlDBfile, csv_name)
		#df = pd.read_csv(csv_name, index_col=0, parse_dates=['created_at'])
		#dfna = df[(df.geolat > 50) & (df.geolong < -90)] #Test on AK
		dfna = df[(df.geolat > 20) & (df.geolong < -60)] #limit to North America

		#Make set of unique coords
		gps_set = set(zip(dfna.geolat, dfna.geolong))

		print ("There are %d total coordinates to look into." % (len(gps_set)))

		#If partial dictionary exists, add to that.
		if os.path.exists(gpsPklFilename+'INCOMPLETE'):
			with open(gpsPklFilename+'INCOMPLETE', 'r') as f:
				geodict = pickle.load(f)
			gps_set = gps_set.difference(geodict.keys())
			print ("Of these, %d have been assigned, leaving %d more to look into."\
				% (len(geodict), len(gps_set)))
		
		return makeGeoDict(gps_set, geodict, gpsPklFilename)


if __name__ == '__main__':
	getGeoDict('data/tweets_NYbox.db','data/tweets_0426.csv','data/gps_dict.pkl')
