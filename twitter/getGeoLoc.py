from __future__ import division, print_function
import pandas as pd
import geopy, pickle, time, accessSQLdb
#import re
#import geopy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
#import pickle




def save_dict(locsDict, pkl_filename, final = True):
	if not final:
		pkl_filename = 'UNFINISHED'+gps_filename
	with open(pkl_filename, 'w') as f:
		pickle.dump(locsDict, f, pickle.HIGHEST_PROTOCOL)

def main():
	df = accessSQLdb.getFromSql(sqlDBfile, csv_name)
	#df = pd.read_csv(csv_name, index_col=0, parse_dates=['created_at'])
	dfna = df[(df.geolat > 50) & (df.geolong < -90)] #Test on AK
	#dfna = df[(df.geolat > 20) & (df.geolong < -60)] #limit to North America

	#Make set of unique coords
	gps_set = set(zip(dfna.geolat, dfna.geolong))
	num_coords = len(gps_set)
	print ("There are %d coordinates to look into." % num_coords)

	geolocator = Nominatim()

	geodict = {}	

	for i, gps_tuple in enumerate(gps_set):
		#x is coordinate as tuple
		try:
			geodict[gps_tuple] = geolocator.reverse(str(gps_tuple)[1:-1]).address
			time.sleep(1)
			if ((i+1)%100 == 0):
				print("Checked %4d (%4.1f%%) so far." %((i+1),((i+1)/num_coords)))
				save_dict(geodict, gps_filename, final = False)

		except GeocoderTimedOut as e:
			print("Error: geocode failed on input #%d = %s with message %s."%(i, gps_tuple, e.message))
			print("Saving incomplete dictionary.")
			save_dict(geodict, gps_filename, final = False)

	save_dict(geodict, gps_filename)

if __name__ == '__main__':
	sqlDBfile = 'tweets_NYbox.db'
	csv_name = 'tweets_0426.csv'
	
	gps_filename = 'gps_dict.pkl'

	main()
	print ("ughghgh")
