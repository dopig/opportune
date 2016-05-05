from __future__ import division, print_function
import pandas as pd
import sqlite3, re
import os.path


def cleanText(text):
    text = re.sub(r"\r"," ", text).lower()
    return re.sub( '\s+', ' ', text).strip()  #This removes excess spaces

def getFromSql(sqlDBfile, csv_name):
	'''Loads csv_name (csv) if it already exists,
	otherwise opens sqlDBfile (sql) and creates csv_name.
	Either way, passes back a csv.'''


	if not os.path.exists(csv_name):
		#If CSV doesn't exist, connect to DB.
		conn = sqlite3.connect(sqlDBfile)
		df_new = pd.read_sql("""SELECT * from tweets WHERE content NOT LIKE 'RT @%'""",
		                 conn, parse_dates=['created_at'])
		conn.close()

		#Get rid of '\r' in content that gums up saving/loading csv
		content = df_new.content.apply(cleanText)
		df_new['content'] = content

		#Save CSV
		df_new.to_csv(csv_name, encoding = 'utf-8')
		print("'%s' file created successfully." %csv_name)

	try:
		#Load it and check if matches expected shape.
		df = pd.read_csv(csv_name, index_col=0, parse_dates=['created_at'])
		print("CSV file loaded and parsed correctly.")

		if df.shape == (1087421, 9):
			print ("DataFrame shape matches expected shape of (1087421, 9).\n")
		else:
			print ("DataFrame shape %s differs from expected shape of (1087421, 9).\n" % str(df.shape))
	except:
		print ("CSV file cannot be loaded!  Look into encoding and retry.")
		raise SystemExit()

	return(df)

if __name__ == '__main__':
	getFromSql('data/tweets_NYbox.db', 'data/tweets_0426.csv')

