from __future__ import print_function, division
import pandas as pd
import numpy as np
from textblob import TextBlob
from time import time
import sqlite3, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF


def cleanRateText(df):
    clean_content = []
    polarity = []

    for c in df.content:
        text = re.sub(r"\r"," ", c).lower()
        text = re.sub( '\s+', ' ', text).strip()  #This removes excess spaces
        clean_content.append(text)
        polarity.append(TextBlob(text).sentiment.polarity)

    df['content'] = clean_content
    df['polarity'] = polarity
    return df


def getSentimentCSV(fileName = 'data/tweetsPlusSen.csv'):
    try:
        df = pd.read_csv(fileName, index_col = 0)

    except: 
        conn = sqlite3.connect('data/tweets_NYbox.db')#'tweets_afternoon.db')
        df = pd.read_sql("""SELECT * from tweets WHERE content NOT LIKE 'RT @%'""",
                         conn, parse_dates=['created_at'])
        conn.close()
        
        #Get rid of '\r' in content that gums up saving/loading csv and rate content
        df = cleanRateText(df)
        df.to_csv(fileName, encoding = 'utf-8')
        print('\a')

    return df


def tweetNMF(df):
    def print_top_words(model, feature_names, n_top_words):
        for topic_idx, topic in enumerate(model.components_):
            print("Topic #%d:" % topic_idx)
            print(" ".join([feature_names[i]
                            for i in topic.argsort()[:-n_top_words - 1:-1]]))
        print()

    n_samples = len(df)
    n_features = 1000
    n_topics = 4
    n_top_words = 3

    data_samples = df.content.values
    print("Extracting tf-idf features for NMF...")
    tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, #max_features=n_features,
                                       stop_words='english')
    t0 = time()
    tfidf = tfidf_vectorizer.fit_transform(data_samples)
    print("done in %0.3fs." % (time() - t0))


    # Fit the NMF model
    print("Fitting the NMF model with tf-idf features,"
          "n_samples=%d and n_features=%d..."
          % (n_samples, n_features))
    t0 = time()
    nmf = NMF(n_components=n_topics, random_state=1, alpha=.1, l1_ratio=.5).fit(tfidf)
    #exit()
    print("done in %0.3fs." % (time() - t0))

    print("\nTopics in NMF model:")
    tfidf_feature_names = tfidf_vectorizer.get_feature_names()
    print_top_words(nmf, tfidf_feature_names, n_top_words)

def printHTMLstickers(stickers):
    hList = []
    for i in range(1,11):
        s = stickers.iloc[i]
        hList.append("<li><b> %s: </b> %s </li>\n" % (s.location, s.content.strip()))
    print("".join(hList))


def main():
    df = getSentimentCSV()

    #Select tweets with negative sentiment that mention polling.
    negPolls = df[(df.polarity < -0.6) & (df.content.str.contains("polling|delay|lines|slow"))]#|delay|lines|slow")]
    print("There are %d negative (polarity < -0.6) tweets about 'polling|delay|lines|slow'." % len(negPolls))
    tweetNMF(negPolls)

    stickers = negPolls[negPolls.content.str.contains('stickers')]
    printHTMLstickers(stickers)





if __name__ == '__main__':
    main()
