#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared constants and utilities for various scripts that handle interacting with
the @false_trump account on Twitter, including those accessible to its
web page.
"""

import glob, datetime, pickle, csv, random, os


force_download = False      # Set to True to always check for new tweets from Trump .
force_tweet = True          # Skip the dice roll; definitely post a new tweet every time the script runs.

base_dir = '/TrumpTweets'
data_dir = '%s/data' % base_dir
data_store = '%s/TrumpTweets_data.pkl' % data_dir
tweets_store = "%s/our_tweets.csv" % data_dir
DMs_store = '%s/seen_DMs.pkl' % data_dir
mentions_store = '%s/seen_mentions.pkl' % data_dir
donnies_tweets_dir = "%s/donnies_tweets" % data_dir

our_minimal_tweets = '/~patrick/projects/TrumpQuiz/false_trump.csv'     # Where to export our selected tweets for the web quiz: local folder 
donnies_minimal_tweets = '/~patrick/projects/TrumpQuiz/trump.csv'       # same, for selected tweets of Trump.

answer_counts = '/~patrick/projects/TrumpQuiz/stats.csv'                # Location of file to store the answer count statistics.

donnie_plaintext_tweets = '%s/donnie_plaintext_tweets.txt' % data_dir
our_plaintext_tweets = '%s/our_plaintext_tweets.txt' % data_dir

programmer_twitter_id = 'patrick_mooney'  # That's me, the author of this script: @patrick_mooney
target_twitter_id = 'realDonaldTrump'  # That's the person whose tweets we're monitoring and imitating: @realDonaldTrump
my_twitter_id = 'false_trump'  # That's the Twitter username under which the script posts: @false_trump


# Miscellaneous convenience functions
def get_tweet_url(account, id):
    """Given a tweet ID and the name of the associated ACCOUNT, generate a URL for
    a tweet.
    """
    return "https://twitter.com/%s/status/%s" % (account, id)

# This function is responsible for picking a tweet at random from a specified archive of tweets.
def get_random_tweet(source_file):
    """Get a random tweet from the .csv archive whose path is passed in as
    SOURCE_FILE.
    """
    with open(source_file, newline='') as the_archive:
        csvreader = csv.reader(the_archive, dialect='unix')
        return dict(zip(['text', 'id', 'date' ], random.choice(list(csvreader))))


# This next group of functions maintains 
def _create_stats_file():
    """For the sake of being explicit:
      trump_right means USER CORRECTLY IDENTIFIED A QUOTE AS COMING FROM DONALD TRUMP
      trump_wrong means USER SAID IT WAS FROM DONALD TRUMP, BUT THAT WAS WRONG
    
    Same for algorithm_right and algorithm_wrong.
    """
    empty_counts = {
        'trump_right': 0,
        'trump_wrong': 0,
        'algorithm_right': 0,
        'algorithm_wrong': 0}
    with open(answer_counts, 'w', newline='') as f:
        writer = csv.writer(stats_file)
        for which_key in empty_counts:
            writer.writerow([which_key, empty_counts[which_key]])

def get_stats_dictionary():
    """Returns a dictionary recording guess counts."""
    with open(answer_counts, newline='') as stats_file:
        return {rows[0]:int(rows[1]) for rows in csv.reader(stats_file)}

def bump_count(which_key):
    """Increases the count of """
    try:
        fd_file = os.open(answer_counts, (os.O_RDWR | os.O_EXCL))
    except FileNotFoundError:
        _create_stats_file()
        fd_file = os.open(answer_counts, (os.O_RDWR | os.O_EXCL))
    stats_file = os.fdopen(fd_file, 'r+', newline="")
    the_stats = {rows[0]:int(rows[1]) for rows in csv.reader(stats_file)}
    the_stats[which_key] += 1
    stats_file.seek(0)
    stats_file.truncate()
    writer = csv.writer(stats_file)
    for which_key in the_stats:
        writer.writerow([which_key, the_stats[which_key]])
    stats_file.close()          # I take it we don't need to separately close the file descriptor.
    
    

if __name__ == "__main__":
    import trump_maint as tm
    import text_handling as th
    the_text = tm.get_donnies_tweet_text()
    th.print_indented(the_text)
