#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A script to download Donald Trump's recent tweets and filter them in ways that
create a textual archive suitable for using for my Make America Sad! Again
Twitter parody account.
"""


import datetime
import glob
import random
import html
import pickle

import tweepy   # https://github.com/tweepy/tweepy

# An unshared file that contains my authentication constants for various social media platforms.
from social_media_auth import personalTwitter_client
Trump_client = personalTwitter_client   # Change this when Twitter finally fixes the new-API-key problem

import sentence_generator as sg         # https://github.com/patrick-brian-mooney/markov-sentence-generator
import text_handling as th              # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/text_handling.py


debugging = True
force_download = False                  # Set to True to always update tweets .

base_dir = '/TrumpTweets'
data_store = '%s/TrumpTweets_data.pkl' % base_dir

markov_length = 2

programmer_twitter_id = 'patrick_mooney'    # That's me, the author of this script

the_API = None


def _get_data_store():
    """Internal function to get the entire stored data dictionary. If the data
    storage dictionary cannot be read, create a new, empty dictionary.
    """
    try:
        with open(data_store, 'rb') as the_data_file:
            return pickle.load(the_data_file)
    except Exception:
        if debugging: th.print_wrapped('WARNING: Data store does not exist or cannot be read, creating ...')
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
    """Retrieves a configuration variable from the data_store file. Not meant to be
    easily user-editable. If the KEYNAME is not in the data store, adds a KEYNAME
    entry with value None and returns None. If it modifies the data store in this
    way, it then writes the data store back to disk. 
    """
    try:
        return _get_data_store()[keyname]
    except KeyError:
        if debugging: th.print_wrapped('WARNING: attempted to get undefined data key "%s"; initializing to None' % keyname)
        set_data_value(keyname, None)
        return None

def _get_new_API():
    """Get an instance of the Tweepy API object to work with.
    """
    auth = tweepy.OAuthHandler(Trump_client['consumer_key'], Trump_client['consumer_secret'])
    auth.set_access_token(Trump_client['access_token'], Trump_client['access_token_secret'])
    return tweepy.API(auth)
        
def get_API():
    """Return the global variable the_API after (if necessary) initializing it.
    """
    global the_API
    if not the_API:
        the_API = _get_new_API()
    return the_API

def get_new_tweets(screen_name='realDonaldTrump', oldest=-1):
    """Get those tweets newer than the tweet whose ID is specified as the OLDEST
    parameter from the account SCREEN_NAME.
    """
    # get most recent tweets (200 is maximum possible at once)
    new_tweets = get_API().user_timeline(screen_name=screen_name, count=200)
    ret = new_tweets.copy()

    oldest_tweet = ret[-1].id - 1   # save the id of the tweet before the oldest tweet

    # keep grabbing tweets until there are no tweets left
    while len(new_tweets) > 0:
        if debugging: print("getting all tweets before ID #%s" % (oldest_tweet), end='')
        new_tweets = get_API().user_timeline(screen_name = screen_name, count=200, max_id=oldest_tweet)
        ret.extend(new_tweets)
        oldest_tweet = ret[-1].id - 1
        if debugging: print("    ...%s tweets downloaded so far" % (len(ret)))
    set_data_value('newest_tweet_id', max([t.id for t in ret]))
    return [t for t in ret if (t.id > oldest)]

def get_newest_tweet_id():
    """Get the ID of the newest tweet that has been received and massaged.
    """
    try:
        return get_data_value('newest_tweet_id') or -1
    except Exception:
        return -1
        
def get_last_update_date():
    """Get the last time that the database was updated.
    """
    try:
        return get_data_value('last_update_date') or datetime.datetime.min
    except Exception:
        return datetime.datetime.min

def get_newest_mention_id():
    """Return the ID of the most recent @mention the program is aware of and has
    dealt with.
    """
    try:
        return get_data_value('last_mention_id') or -1
    except Exception:
        return -1

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
            return not (th.strip_leading_and_trailing_punctuation(at_mentions[0].strip()).strip().lower() == 'realdonaldtrump')
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
                         ['V.P.', 'V․P․'],          # Again
                         ['Mr.', 'Mr․'],            # Again
                         ['Dr.', 'Dr․'],            # Again
                         ['Mrs.', 'Mrs․'],          # Again
                         ['Rev.', 'Rev․'],          # Again
                        ]
    changed = True              # Be sure to run at least once.
    while changed:              # Repeatedly perform all substitutions until none of them change anything at all.
        orig_tweet = the_tweet.text[:]
        for which_replacement in substitution_list:
            the_tweet.text = the_tweet.text.replace(which_replacement[0], which_replacement[1])
        changed = ( orig_tweet != the_tweet.text )
    the_tweet.text = html.unescape(the_tweet.text)    
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
    with open('%s/tweets/%s.txt' % (base_dir, datetime.datetime.now().isoformat()), 'w') as f:
        f.writelines(['%s\n' % tweet.text for tweet in the_tweets])
    set_data_value('last_update_date', datetime.datetime.now())     # then, update the database of tweet-record filenames and ID numbers

def _num_tweet_files():
    """Convenience function to return the number of files in which The Donald's
    tweets are stored.
    """
    return len(glob.glob('%s/tweets/*txt' % base_dir))

def update_tweet_collection_if_necessary():
    """Once in a while, import new tweets encoding the brilliance that The Donald &
    his team have graced the world by sharing. 
    """
    if _num_tweet_files == 0 or (datetime.datetime.now() - get_last_update_date()).days > 30 or random.random() < 0.03 or force_download:
        if debugging: print("INFO: updating tweet collection")
        t = get_new_tweets(screen_name='realDonaldTrump', oldest = get_newest_tweet_id())
        t = massage_tweets(t)
        save_tweets(t)

def get_tweet(starts, the_mapping):
    """Produces a tweet by repeatedly calling the text generator with varying
    parameters until it coughs up something in the right length range. 
    """
    the_tweet = ' ' * 160
    while len(the_tweet) not in range(20,141):
        sents = random.choice(range(2,5))
        if debugging: print("Generating a tweet (%d sentences) ..." % sents, end="")
        the_tweet = sg.gen_text(the_mapping, starts, markov_length=markov_length, sentences_desired=sents)
        if debugging: print("length is %d" % len(the_tweet))
    return the_tweet

def tweet(text):
    """Post a tweet. Currently, it doesn't actually do so; it just prints it to stdout. 
    """
    th.print_indented(text)
    
def post_reply(text, user_id, tweet_id):
    """Post a reply tweet. TWEET_ID is the id of the tweet that this tweet is a reply
    to; the USER_ID is the person to whom we are replying, and the user_id is
    automatically prepended to the beginning of TEXT before posting.
    
    Currently does not actually post the tweet, but just prints to stdout. 
    """
    if debugging: th.print_wrapped("INFO: posting tweet: @%s %s  ----  in reply to tweet ID# %d" % (user_id, text, tweet_id))    
    # get_API().update_status("@%s %s" % (user_id, text), in_reply_to_status_id = tweet_id)

def modified_retweet(text, user_id, tweet_id):
    if debugging: th.print_wrapped("%s\n\nhttps://twitter.com/%s/status/%s" % (text, user_id, tweet_ID))
    # get_API().update_status("%s\n\nhttps://twitter.com/%s/status/%s" % (text, user_id, tweet_ID))

def process_command(command, issuer_id, tweet_id):
    """Process a command coming from my own twitter account.
    """
    command_parts = [c.strip().lower() for c in command.strip().split()]
    if command_parts[0] in ['stop', 'quiet', 'silence']:
        set_data_value('stopped', True)
        post_reply('You got it, sir, halting tweets per your command.', user_id=issuer_id, tweet_id=tweet_id)
    elif command_parts[0] in ['start', 'verbose', 'go', 'loud', 'begin']:
        set_data_value('stopped', False)
        post_reply('Yessir, beginning tweeting again per your command.', user_id=issuer_id, tweet_id=tweet_id)     
    else:
        post_reply("Sorry, sir. I didn't understand that.", user_id=issuer_id, tweet_id=tweet_id)     

def handle_mention(mention):
    """Process the mention in whatever way is appropriate.
    """
    if debugging:
        th.print_wrapped("INFO: Handling mention ID #%d" % mention.id)
        th.print_indented("text is: %s" % mention.text)
        th.print_indented("user is: @%s" % mention.user.screen_name)
    if mention.user.screen_name.strip('@').lower() == programmer_twitter_id.strip('@').lower():
        process_command(mention.text, issuer_id=programmer_twitter_id, tweet_id=mention.id)
    elif mention.user.screen_name.strip('@').lower().strip() == 'realdonaldtrump':
        if debugging: print("Oh my! The Donald is speaking! Click your jackboots together and salute!")
        modified_retweet('LOL\n\n', user_id="realDonaldTrump", tweet_id=mention.id)
    else:
        if debugging:
            th.print_wrapped('WARNING: unhandled mention from user @%s' % mention.user.screen_name)
            th.print_indented("the tweet is: %s" % mention.text)

def check_mentions():
    """A stub to check for any @mentions and, if necessary, reply to them.
    """
    for mention in [m for m in get_API().mentions_timeline(count=100) if m.id > get_newest_mention_id()]:
        handle_mention(mention)
        set_data_value('last_mention_id', max(mention.id, get_newest_mention_id()))

def set_up():
    """Perform pre-tweeting tasks. Currently (as of 1 Jan 2017), it just updates the
    collection of stored tweets, but in the future it will check for other types of
    things, like user interaction.
    """
    update_tweet_collection_if_necessary()
    check_mentions()


if __name__ == '__main__':
    if get_data_value('stopped'):
        if debugging: th.print_wrapped('Aborting: user data key "stopped" is set.')
        sys.exit(0)
    set_up()
    donnies_words = [][:]
    for the_file in glob.glob('%s/tweets/*txt' % base_dir):
        donnies_words += sg.word_list(the_file)
    starts, the_mapping = sg.buildMapping(donnies_words, markov_length=markov_length)
    tweet(get_tweet(starts, the_mapping))