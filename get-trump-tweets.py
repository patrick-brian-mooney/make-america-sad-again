#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A script to download Donald Trump's recent tweets and filter them in ways that
create a textual archive suitable for using for my Make America Sad! Again
Twitter parody account.
"""

import csv
import time

import tweepy   # https://github.com/tweepy/tweepy

# An unshared file that contains my authentication constants for various social media platforms.
from social_media_auth import personalTwitter_client
Trump_client = personalTwitter_client   # Change this when Twitter finally fixes the new-API-key problem

import sentence_generator as sg         # https://github.com/patrick-brian-mooney/markov-sentence-generator


debugging = True

base_dir = '/TrumpTweets'


def get_new_tweets(screen_name='realDonaldTrump', oldest=-1):
    # authorize Twitter & initialize Tweepy
    auth = tweepy.OAuthHandler(Trump_client['consumer_key'], Trump_client['consumer_secret'])
    auth.set_access_token(Trump_client['access_token'], Trump_client['access_token_secret'])
    api = tweepy.API(auth)

    # get most recent tweets (200 is maximum possible at once)
    new_tweets = api.user_timeline(screen_name=screen_name, count=200)
    ret = new_tweets.copy()
    
    # save the id of the tweet before the oldest tweet
    oldest_tweet = ret[-1].id - 1

    # keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        if debugging: print("getting all tweets before ID #%s" % (oldest_tweet), end='')
        new_tweets = api.user_timeline(screen_name = screen_name, count=200, max_id=oldest_tweet)
        ret.extend(new_tweets)
        oldest_tweet = ret[-1].id - 1

        if debugging: print("    ...%s tweets downloaded so far" % (len(ret)))
    
    return [t for t in ret if (t.id > oldest)]

def save_tweets(the_tweets):
    # save the tweets
    the_time = time.strftime("%Y-%m-%d-%H_%M_%S")
    with open('%s/tweets/%s.txt' % (base_dir, the_time), 'w') as f:
        f.writelines(['%s\n' % tweet.text for tweet in the_tweets])
    
    # update the database of tweet-record filenames and ID numbers
    try:
        with open('%s/tweets/index.csv' % base_dir, newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            database = list(csvreader)
        database.append([the_time, max([t.id for t in the_tweets])])    # Add filename and its largest ID to the databaseids
    except Exception as e:
        database = [][:]
        print('WARNING: unable to read index of stored-tweet files; using empty list ...')
    try:
        with open('%s/tweets/index.csv' % base_dir, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(database)
    except Exception as e:
        print('WARNING: unable to update index of stored-tweet files')    

if __name__ == '__main__':
    #pass in the username of the account you want to download
    t = get_new_tweets()
    save_tweets(t)