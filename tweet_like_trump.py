#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A script to download Donald Trump's recent tweets and filter them in ways that
create a textual archive suitable for using for my Make America Sad! Again
Twitter parody account. It maintains a list of tweets it has seen after
massaging them and posts tweets to the MAS!A account; it also has some limited
abilities to engage in interactions with other accounts.

This script is PRE-ALPHA SOFTWARE, and certainly contains many defects, some of
which may be serious. The author accepts no liability for the effects of running
this script on your computer.

This program is copyright by Patrick Mooney; it is free software, licensed
under the GPL, either version 3 or (at your option) any later version. See the
file LICENSE.md for details.
"""


import datetime, sys, pprint, glob, random, html, pickle

import tweepy                               # https://github.com/tweepy/tweepy

from social_media_auth import Trump_client
        # That's an unshared file that contains my authentication constants for various social media platforms.

import social_media as sm                   # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/social_media.py
import sentence_generator as sg             # https://github.com/patrick-brian-mooney/markov-sentence-generator
import text_handling as th                  # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/text_handling.py
import patrick_logger                       # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py
from patrick_logger import log_it

patrick_logger.verbosity_level = 1          # As of 9 January 2017, 1 is the highest meaningful level for this script
force_download = False                      # Set to True to always check for new tweets from Trump .

base_dir            = '/TrumpTweets'
data_store          = '%s/TrumpTweets_data.pkl' % base_dir
tweets_store        = "%s/tweets.txt" % base_dir
donnies_tweets_dir  = "%s/tweets" % base_dir

markov_length = 2

programmer_twitter_id = 'patrick_mooney'    # That's me, the author of this script: @patrick_mooney
target_twitter_id = 'realDonaldTrump'       # That's the person whose tweets we're monitoring and imitating: @realDonaldTrump
my_twitter_id = 'false_trump'               # That's the Twitter username under which the script posts: @herr_drumpf


def _get_new_API():
    """Get an instance of the Tweepy API object to work with.
    """
    auth = tweepy.OAuthHandler(Trump_client['consumer_key'], Trump_client['consumer_secret'])
    auth.set_access_token(Trump_client['access_token'], Trump_client['access_token_secret'])
    return tweepy.API(auth)

the_API = _get_new_API()


def _get_data_store():
    """Internal function to get the entire stored data dictionary. If the data
    storage dictionary cannot be read, create a new dictionary with default
    values.
    """
    try:
        with open(data_store, 'rb') as the_data_file:
            return pickle.load(the_data_file)
    except Exception:
        log_it('WARNING: Data store does not exist or cannot be read, creating ...')
        the_data = {'purpose': 'data store for the TrumpTweets project at @MakeAmericaSad!Again',
                    'program author': 'Patrick Mooney',
                    'script URL': 'https://github.com/patrick-brian-mooney/make-america-sad-again',
                    'author twitter ID': '@patrick_mooney',
                   }
        with open(data_store, 'wb') as the_data_file:
            pickle.dump(the_data, the_data_file)
        return the_data

def set_data_value(keyname, value):
    """Store a VALUE, by KEYNAME, in the persistent data store. This data store is
    read from disk, modified, and immediately written back to disk. This is a
    naive function that doesn't worry about multiple simultaneous attempts to
    access the store: there should never be any. (This script should be the only
    process accessing the file, and there should only be one invocation running
    at a time.
    """
    the_data = _get_data_store()
    the_data[keyname] = value
    with open(data_store, 'wb') as the_data_file:
        pickle.dump(the_data, the_data_file)

def get_data_value(keyname):
    """Retrieves a configuration variable from the data_store file, which is not
    meant to be easily user-editable. If the KEYNAME is not in the data store,
    adds a KEYNAME entry with value None and returns None. If it modifies the data
    store in this way, it then writes the data store back to disk.
    """
    try:
        return _get_data_store()[keyname]
    except KeyError:
        log_it('WARNING: attempted to get undefined data key "%s"; initializing to None' % keyname)
        set_data_value(keyname, None)
        return None

def get_new_tweets(screen_name=target_twitter_id, oldest=-1):
    """Get those tweets newer than the tweet whose ID is specified as the OLDEST
    parameter from the account SCREEN_NAME.
    """
    # get most recent tweets (200 is maximum possible at once)
    new_tweets = the_API.user_timeline(screen_name=screen_name, count=200)
    ret = new_tweets.copy()

    oldest_tweet = ret[-1].id - 1   # save the id of the tweet before the oldest tweet

    # keep grabbing tweets until there are no tweets left
    while len(new_tweets) > 0 and oldest < new_tweets[0].id:
        log_it("getting all tweets before ID #%s" % (oldest_tweet))
        new_tweets = the_API.user_timeline(screen_name = screen_name, count=200, max_id=oldest_tweet)
        ret.extend(new_tweets)
        oldest_tweet = ret[-1].id - 1
        log_it("    ...%s tweets downloaded so far" % (len(ret)))
    set_data_value('newest_tweet_id', max([t.id for t in ret]))
    return [t for t in ret if (t.id > oldest)]

def get_key_value_with_default(key_name, default=None):
    try:
        return get_data_value(key_name) or default
    except Exception:
        return default

def get_newest_tweet_id():
    """Get the ID of the newest tweet that has been received and massaged.
    """
    return get_key_value_with_default('newest_tweet_id', default=-1)

def get_last_update_date():
    """Get the last time that the database was updated.
    """
    return get_key_value_with_default('last_update_date', default=datetime.datetime.min)

def get_newest_mention_id():
    """Return the ID of the most recent @mention the program is aware of and has
    dealt with.
    """
    return get_key_value_with_default('last_mention_id', default=-1)

def get_newest_dm_id():
    """Returns the ID of the most recently seen DM.
    """
    return get_key_value_with_default('last_dm_id', default=-1)

def filter_tweet(tweet_text):
    """Returns True if the tweet should be filtered (i.e., eliminated), False if it
    should not be filtered (i.e., should remain in the list).

    Currently, just eliminates tweets with URLs and tweets that @mention any
    account other than @realDonaldTrump (i.e., when The Donald talks about, or to,
    anyone else -- we don't want this account interacting with people just because
    The Donald does. The Donald is a terrible model for appropriate behavior).

    However, there may need to be more nuanced behavior in the future.
    """
    if 't.co' in tweet_text:    # All URLs coming from Twitter contain Twitter's redirection domain.
        return True             # At this time, the text generator doesn't deal well with input text containing URLs.
    elif '@' in tweet_text:     # Since more than one @mention can occur in a tweet ...
        at_mentions = list(set([w for w in tweet_text.split() if '@' in w]))   # Make a list of all unique @mentions
        if len(at_mentions) == 1:
            return not (th.strip_leading_and_trailing_punctuation(at_mentions[0].strip()).strip().lower() == target_twitter_id.strip().lower())
        else:                   # Filter out tweets mentioning more than one person:
            return True         # by def'n, they're not just The Donald being self-aggrandizing.
    return False

def normalize(the_tweet):
    """Convert THE_TWEET into a normalized form, based on the replacements in
    SUBSTITUTION_LIST (specified below). All substitutions are applied repeatedly,
    in the order they appear in the list, until none of them produces a change.
    HTML/XML entities are also unescaped, and any necessary other transformations
    are applied.

    THE_TWEET is a Tweepy tweet object, not a string.
    """
    substitution_list = [['\n', ' '],               # Newline to space
                         ['  ', ' '],               # Two spaces to one space
                         ['U.S.A.', 'U․S․A․'],      # Periods to one-dot leaders
                         ['U. S. A.', 'U․S․A․'],    # Periods to one-dot leaders, remove spaces
                         ['U. S.', 'U․S․'],         # Periods to one-dot leaders, remove spaces
                         ['U.S.', 'U․S․'],          # Periods to one-dot leaders
                         ['P․M․', 'P․M․'],          # Again
                         ['A․M․', 'A․M․'],          # Again
                         ['V.P.', 'V․P․'],          # Again
                         ['Mr.', 'Mr․'],            # Again
                         ['Dr.', 'Dr․'],            # Again
                         ['Mrs.', 'Mrs․'],          # Again
                         ['Ms.', 'Ms․'],            # Again
                         ['Rev.', 'Rev․'],          # Again
                        ]
    the_tweet.text = html.unescape(th.multi_replace(the_tweet.text, substitution_list))
    return the_tweet

def massage_tweets(the_tweets):
    """Make the tweets more suitable for feeding into the Markov-chain generator.
    Currently, this just drops tweets that have URLS or @mentions, but a more
    nuanced approach would be great in the future.
    """
    ret = [normalize(t) for t in the_tweets if not filter_tweet(t.text)]
    return ret

def save_tweets(the_tweets):
    """Save the text from THE_TWEETS to a text file, and update the stored data.
    THE_TWEETS is a list of Tweets.
    """
    if len(the_tweets) == 0:        # If there are no new tweets, don't do anything
        return
    with open('%s/tweets/%s.txt' % (donnies_tweets_dir, datetime.datetime.now().isoformat()), 'w') as f:
        f.writelines(['%s\n' % tweet.text for tweet in the_tweets])
    set_data_value('last_update_date', datetime.datetime.now())     # then, update the database of tweet-record filenames and ID numbers

def _num_tweet_files():
    """Convenience function to return the number of files in which The Donald's
    tweets are stored.
    """
    return len(glob.glob('%s/*txt' % donnies_tweets_dir))

def update_tweet_collection():
    """Update the tweet collection."""
    log_it("INFO: updating tweet collection")
    t = get_new_tweets(screen_name=target_twitter_id, oldest=get_newest_tweet_id())
    t = massage_tweets(t)
    save_tweets(t)

def update_tweet_collection_if_necessary():
    """Once in a while, import new tweets encoding the brilliance that The Donald &
    his team have graced the world by sharing.
    """
    if _num_tweet_files == 0 or (datetime.datetime.now() - get_last_update_date()).days > 30 or random.random() < 0.03 or force_download:
        update_tweet_collection()

def did_donnie_say_it(what):
    """Return True if WHAT has appeared in the Trump tweets we know about, or
    False otherwise.
    """
    ret = False
    donnies_wisdom_files = glob.glob('%s/*txt' % donnies_tweets_dir)
    while not ret and len(donnies_wisdom_files) != 0:   # Check files one by one until we find that donnie said it, or run out of files.
        which_file = donnies_wisdom_files.pop()
        with open(which_file) as the_file:
            ret = what.strip().lower() in [ the_line.strip().lower() for the_line in the_file.readlines() ]
    return ret

def did_we_say_it(what):
    """Return True if we've previously tweeted WHAT, or False otherwise.
    """
    try:
        with open(tweets_store) as the_file:
            return what.strip().lower() in [ line.strip().lower() for line in the_file.readlines ] 
    except Exception:
        return False

def validate_tweet(the_tweet):
    """Return True if the tweet is acceptable according to whatever criteria this
    particular function decides, or False if the tweet is not acceptable.
    
    Currently, the function approves all tweets, unless they meet any of the 
    following criteria:
        
        * length is not in range(20,141)
        * is exactly the same as another tweet by The Donald.
        * is identical to a previous tweet by this account
    """
    if not len(the_tweet) in range(20,141):
        return False
    if did_donnie_say_it(the_tweet):
        return False
    if did_we_say_it(the_tweet):
        return False
    return True

def get_tweet(starts, the_mapping):
    """Produces a tweet by repeatedly calling the text generator with varying
    parameters until it coughs up something in the right length range.
    """
    got_tweet = False
    while not got_tweet:
        sents = random.choice(range(2,5))
        log_it("Generating a tweet (%d sentences) ..." % sents)
        the_tweet = sg.gen_text(the_mapping, starts, markov_length=markov_length, sentences_desired=sents)
        got_tweet = validate_tweet(the_tweet)
        log_it("length is %d" % len(the_tweet))
    return the_tweet

def tweet(text):
    """Post a tweet. Also, add the tweet to the list of tweets created so far by
    the script.
    """
    log_it("Tweet is: %s" % text)
    sm.post_tweet(Trump_client, text)
    try:
        with open(tweets_store) as the_file:
            the_lines = the_file.readlines()
    except Exception:
        the_lines = [][:]
    the_lines += [ text + '\n' ]
    with open(tweets_store, 'w') as the_file:
        the_file.writelines(the_lines) 

def process_command(command, issuer_id, tweet_id):
    """Process a command coming from my own twitter account.
    """
    command_parts = [c.strip().lower() for c in command.strip().split() if not c.strip().startswith('@')]
    if command_parts[0] in ['stop', 'quiet', 'silence']:
        set_data_value('stopped', True)
        sm.send_DM(the_API=the_API, text='You got it, sir, halting tweets per your command.', user=issuer_id)
        log_it('INFO: aborting run because command "%s" was issued.' % command_parts[0])
        sys.exit(0)
    elif command_parts[0] in ['start', 'verbose', 'go', 'loud', 'begin']:
        set_data_value('stopped', False)
        sm.send_DM(the_API=the_API, text='Yessir, beginning tweeting again per your command.', user=issuer_id)
    elif command_parts[0] in ['update', 'refresh', 'check', 'reload', 'new']:
        update_tweet_collection()
        sm.send_DM(the_API=the_API, text='You got it, sir: tweet collection updated.', user=issuer_id)
    else:
        sm.send_DM(the_API=the_API, text="Sorry, sir. I didn't understand that.", user=issuer_id)

def handle_mention(mention):
    """Process the mention in whatever way is appropriate.
    """
    log_it("INFO: Handling mention ID #%d" % mention.id)
    log_it("text is: %s" % mention.text)
    log_it("user is: @%s" % mention.user.screen_name)
    if mention.user.screen_name.strip('@').lower() == programmer_twitter_id.strip('@').lower():
        process_command(mention.text, issuer_id=programmer_twitter_id, tweet_id=mention.id)
    elif mention.user.screen_name.strip('@').lower().strip() == target_twitter_id:
        log_it("Oh my! The Donald is speaking! Click your jackboots together and salute!")
        sm.modified_retweet('LOL\n\n', user_id=target_twitter_id, tweet_id=mention.id)
        sm.modified_retweet('LOL\n\n', user_id=target_twitter_id, tweet_id=mention.id)
    else:
        log_it('WARNING: unhandled mention from user @%s' % mention.user.screen_name)
        log_it("the tweet is: %s" % mention.text)

def check_mentions():
    """A stub to check for any @mentions and, if necessary, reply to them.
    """
    for mention in [m for m in the_API.mentions_timeline(count=100) if m.id > get_newest_mention_id()]:
        handle_mention(mention)
        set_data_value('last_mention_id', max(mention.id, get_newest_mention_id()))

def handle_dm(direct_message):
    """Handle a given direct message. Currently, it just treats any DM from me as a
    command, and replies to anyone else with an explanation that it doesn't
    respond usefully to DMs.
    """
    log_it("INFO: Handling direct message ID #%d" % direct_message.id)
    log_it("direct message is:\n\n%s" % pprint.pformat(direct_message))
    log_it("text is: %s" % direct_message.text)
    log_it("user is: @%s" % direct_message.sender_screen_name)
    if direct_message.sender_screen_name.lower().strip('@') == programmer_twitter_id.lower().strip('@'):
        process_command(direct_message.text, issuer_id=programmer_twitter_id, tweet_id=direct_message.id)
    else:
        log_it("WARNING: unhandled DM detected:")
        log_it(pprint.pformat(direct_message))
        log_it("Replying with default message")
        sm.send_DM(the_API=the_API, text="Sorry, I'm a bot and don't understand how to deal with direct messages. If you need to reach my human minder, tweet at @patrick_mooney.", user=direct_message.user.screen_name) 

def check_DMs():
    """Check and handle any direct messages.
    """
    for dm in [dm for dm in the_API.direct_messages(count=100, full_text=True, since_id=get_newest_dm_id()) if dm.id > get_newest_dm_id()]:
        handle_dm(dm) 

def set_up():
    """Perform pre-tweeting tasks. Currently (as of 1 Jan 2017), it just updates the
    collection of stored tweets, but in the future it will check for other types of
    things, like user interaction.
    """
    update_tweet_collection_if_necessary()
    check_mentions()
    check_DMs()


if __name__ == '__main__':
    set_up()
    if get_data_value('stopped'):
        log_it('Aborting: user data key "stopped" is set.')
        sys.exit(0)
    donnies_words = [][:]
    for the_file in glob.glob('%s/*txt' % donnies_tweets_dir):
        donnies_words += sg.word_list(the_file)
    starts, the_mapping = sg.buildMapping(donnies_words, markov_length=markov_length)
    tweet(get_tweet(starts, the_mapping))
