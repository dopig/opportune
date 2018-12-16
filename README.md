# Project to Analyze Voting Resources

## DMV
The DMV project focuses on analyzing the locations of DMV offices in states
that require voter ID.  Do some states place more or less of a burden on their
citizens who are looking for IDs?

#### getDMVs.py
Scrapes data from state DMV websites and uses geopy to get gps
coordinates for all offices.

#### concatDmvCsv.py
Sticks these together.

#### getCountyData.py
Pulls demographs data from the US Census API and from US
Census website.

#### mergePlot7States.py
Merges above data and plots some from 7 states.

## Twitter
The Twitter project focuses on analyzing tweets from (primary) election days to determine what voters are upset about and where those voters are.

#### get_election_tweets.py
Pulled down all English-language public election-related tweets on Tuesday April 26, a primary election day in several northeast states, storing them in a SQLite database.

#### accessSQLdb.py
Accesses SQLite db, and creates csv file.

#### getGeoLoc.py
Pulls all latitude/longitude coordinates from above tweets, and determines addresses for those for northwest of globe (~North America).

#### tweetSentiment.py
Analyzes sentiment in election day tweets and looks for topics that emerge in the negative tweets.


