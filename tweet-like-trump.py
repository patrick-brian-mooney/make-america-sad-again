#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A script to download Donald Trump's recent tweets and filter them in ways that
create a textual archive suitable for using for my Make America Sad! Again
Twitter parody account.
"""

import csv
import time
import glob
import random

import tweepy   # https://github.com/tweepy/tweepy

# An unshared file that contains my authentication constants for various social media platforms.
from social_media_auth import personalTwitter_client
Trump_client = personalTwitter_client   # Change this when Twitter finally fixes the new-API-key problem

import sentence_generator as sg         # https://github.com/patrick-brian-mooney/markov-sentence-generator
import text_handling as th              # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/text_handling.py


debugging = True

base_dir = '/TrumpTweets'

markov_length = 2


def get_new_tweets(screen_name='realDonaldTrump', oldest=-1):
    """Get those tweets newer than the tweet whose ID is specified as the OLDEST
    parameter from the account SCREEN_NAME.
    """
    # set up the Twitter API
    auth = tweepy.OAuthHandler(Trump_client['consumer_key'], Trump_client['consumer_secret'])
    auth.set_access_token(Trump_client['access_token'], Trump_client['access_token_secret'])
    api = tweepy.API(auth)

    # get most recent tweets (200 is maximum possible at once)
    new_tweets = api.user_timeline(screen_name=screen_name, count=200)
    ret = new_tweets.copy()

    oldest_tweet = ret[-1].id - 1   # save the id of the tweet before the oldest tweet

    # keep grabbing tweets until there are no tweets left
    while len(new_tweets) > 0:
        if debugging: print("getting all tweets before ID #%s" % (oldest_tweet), end='')
        new_tweets = api.user_timeline(screen_name = screen_name, count=200, max_id=oldest_tweet)
        ret.extend(new_tweets)
        oldest_tweet = ret[-1].id - 1
        if debugging: print("    ...%s tweets downloaded so far" % (len(ret)))
    return [t for t in ret if (t.id > oldest)]

def get_newest_tweet_id():
    """Get the ID of the newest tweet that appears in the tweet index, which is
    index.csv.
    """
    try:
        with open('%s/tweets/index.csv' % base_dir, newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            return max([int(r[1]) for r in list(csvreader)])
    except Exception:
        return -1
        
def get_last_update_date():
    """Get the last time that the database was updated.
    """
    try:
        with open('%s/tweets/index.csv' % base_dir, newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            #FIXME: this routine is neither complete nor called by anything
    finally:
        pass

def filter_tweet(tweet_text):
    """Returns True if the tweet should be filtered (i.e., eliminated), False if it
    should not be filtered (i.e., should remain in the list).

    Currently, just eliminates tweets with URLs and tweets that @mention any
    account other than @realDonaldTrump (i.e., when The Donald talks about, or to,
    anyone else) -- we don't want this account interacting with people just because
    The Donald does. The Donald is a terrible model for appropriate behavior.
    
    However, there may need to be more nuanced behavior in the future.
    """
    if 't.co' in tweet_text:    # All URLs coming from Twitter contain Twitter's redirection domain.
        return True             # At this time, the text generator doesn't deal well with input text containing URLs.
    elif '@' in tweet_text:     # Since more than one @mention can occur in a tweet ...
        at_mentions = list(set([w for w in tweet_text.split() if '@' in w]))   # Make a list of all unique @mentions
        if len(at_mentions) == 1:
            return not (th.strip_leading_and_trailing_punctuation(at_mentions[0].strip()).strip().lower() == 'realdonaldtrump')
        else:                   # Filter out tweets mentioning more than one person:
            return True         # by def'n, they're not just The Donald being self-aggrandizing.
    return False

def normalize(the_tweet):
    """Convert THE_TWEET into a normalized form, based on the replacements in
    SUBSTITUTION_LIST (specified below).
    
    THE_TWEET is a Tweepy tweet object, not a string.
    """
    substitution_list = [['\n', ' '],   # Newline to space
                         ['  ', ' '],   # Two spaces to one space
                         ]
    changed = True              # Be sure to run at least once.
    while changed:              # Repeatedly perform all substitutions until none of them change anything at all.
        orig_tweet = the_tweet.text[:]
        for which_replacement in substitution_list:
            the_tweet.text = the_tweet.text.replace(which_replacement[0], which_replacement[1])
        changed = ( orig_tweet != the_tweet.text )
    return the_tweet

def massage_tweets(the_tweets):
    """Make the tweets more suitable for feeding into the Markov-chain generator.
    Currently, this just drops tweets that have URLS or @mentions, but a more
    nuanced approach would be great in the future.
    """
    ret = [normalize(t) for t in the_tweets if not filter_tweet(t.text)]
    return ret

def save_tweets(the_tweets):
    """Save the text from THE_TWEETS to a text file, and update the index in
    index.csv to reference the new file created.


    THE_TWEETS is a list of Tweets.
    """
    if len(the_tweets) == 0:        # If there are no new tweets, don't do anything
        return
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
        database = [[the_time, max([t.id for t in the_tweets])]]
        print('WARNING: unable to read index of stored-tweet files; downloading all and creating new list ...')
    try:
        with open('%s/tweets/index.csv' % base_dir, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(database)
    except Exception as e:
        print('WARNING: unable to update index of stored-tweet files')

def update_database_if_necessary():
    if False:        # But be more specific later.
        t = get_new_tweets(screen_name='realDonaldTrump', oldest = get_newest_tweet_id())
        t = massage_tweets(t)
        save_tweets(t)

def get_tweet(starts, the_mapping):
    the_tweet = ' ' * 160
    while len(the_tweet) not in range(1,141):
        the_tweet = sg.gen_text(the_mapping, starts, markov_length=markov_length, sentences_desired=random.choice(range(1,4)))
    return the_tweet
    

if __name__ == '__main__':
    update_database_if_necessary()
    the_words = [][:]
    for the_file in glob.glob('%s/tweets/*txt' % base_dir):
        the_words += sg.word_list(the_file)
    starts, the_mapping = sg.buildMapping(the_words, markov_length=markov_length)
    print(get_tweet(starts, the_mapping))