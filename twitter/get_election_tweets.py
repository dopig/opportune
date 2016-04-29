# The Following Script will download the twitter stream
# and store it in a SQLite database which has already been created 
from __future__ import division, print_function
import tweepy, sqlite3
from datetime import datetime

# database interface
# The Following script creates the database where we will store tweets
conn = sqlite3.connect('data/tweets_NYbox.db')
curs = conn.cursor()
curs.execute("CREATE TABLE IF NOT EXISTS tweets (tid integer, username text, created_at text, content text, location text, source text, geotype text, geolat real, geolong real)")


def stripit(x):
	try:
		return x.strip()
	except:
		return x

class StreamWatcherHandler(tweepy.StreamListener):
	""" Handles all incoming tweets as discrete tweet objects.
	"""
 
	def on_status(self, status):
		"""Called when status (tweet) object received.
		"""
		try:
			tid = status.id_str
			usr = stripit(status.author.screen_name)
			lang = stripit(status.lang)
			txt = stripit(status.text)
			location = stripit(status.user.location)
			src = stripit(status.source)
			cat = status.created_at
			geo = stripit(status.geo)
			if geo == None:
				geotype = geolat = geolong = None
			else:
				print (datetime.now(), geo)
				#Geo is a dictionary!
				geotype = geo['type']
				(geolat, geolong) = geo['coordinates']
			# Now that we have our tweet information, let's stow it away in our 
			# sqlite database
			curs.execute("insert into tweets (tid, username, created_at, content, location, source, geotype, geolat, geolong) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",
						  (tid, usr, cat, txt, location, src, geotype, geolat, geolong))
			conn.commit()
		except Exception as e:
			# Most errors we're going to see relate to the handling of UTF-8 messages (sorry)
			print(e)
 
	def on_error(self, status_code):
	   print('An error has occured! Status code = %s' % status_code)
	   return True
 
def main():
	# establish stream
	with open('../keys/twitterKey.csv','r') as f:
		(consumer_key, consumer_secret, access_token, access_token_secret) = \
			f.read().strip().split(",")
	auth1 = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
	auth1.set_access_token(access_token, access_token_secret)
 
	def start_stream():
		while True:
			try:
				print ("Establishing stream at %s ..." % str(datetime.now()))
				stream = tweepy.Stream(auth1, StreamWatcherHandler(), timeout=None)
				print ("Done")
				keywords = ['vote', 'voting', 'election', 'poll', 'voted', 'votes',\
				 'polling', 'primary', 'hillary', 'bernie', 'sanders', 'clinton', 
				 'trump', 'kasich', 'ted cruz']
				stream.filter(track=keywords, languages=["en"])
			except: 
					continue
	start_stream()

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print ("Disconnecting from database... ")
		conn.commit()
		conn.close()
		print ("Done at %s" % str(datetime.now()))