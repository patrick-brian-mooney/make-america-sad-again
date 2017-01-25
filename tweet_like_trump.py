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

import datetime, sys, pprint, random, html, csv

import tweepy   # https://github.com/tweepy/tweepy

from social_media_auth import Trump_client
# That's an unshared file that contains my authentication constants for various social media platforms.

import social_media as sm           # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/social_media.py
import sentence_generator as sg     # https://github.com/patrick-brian-mooney/markov-sentence-generator
import text_handling as th          # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/text_handling.py
import patrick_logger               # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py
from patrick_logger import log_it

import trump_utils as tu
import trump_maint as tm


patrick_logger.verbosity_level = 2  # As of 14 January 2017, 3 is the highest meaningful level for this script

markov_length = 2

def _get_new_API():
    """Get an instance of the Tweepy API object to work with."""
    auth = tweepy.OAuthHandler(Trump_client['consumer_key'], Trump_client['consumer_secret'])
    auth.set_access_token(Trump_client['access_token'], Trump_client['access_token_secret'])
    ret = tweepy.API(auth)
    ret.wait_on_rate_limit, ret.wait_on_rate_limit_notify = True, True
    return ret

the_API = _get_new_API()


# Convenience functions to get specific data from the data store.
def get_newest_tweet_id():
    """Get the ID of the newest tweet that has been received and massaged. As a
    special case, sets the value to -1, then returns -1, if there are no files
    in the store of seen, postprocessed tweets.
    """
    if tm._num_tweet_files() == 0:
        tm.set_data_value('newest_tweet_id', -1)
    return tm.get_key_value_with_default('newest_tweet_id', default=-1)

def get_last_update_date():
    """Get the last time that the database was updated."""
    return tm.get_key_value_with_default('last_update_date', default=datetime.datetime.min)

def get_newest_mention_id():
    """Return the ID of the most recent @mention the program is aware of and has
    dealt with.
    """
    return tm.get_key_value_with_default('last_mention_id', default=-1)

def get_newest_dm_id():
    """Returns the ID of the most recently seen DM."""
    if tm.get_key_value_with_default('last_dm_id', default=-1) < max(tm.get_id_set(tu.DMs_store)):
        tm.set_data_value('last_dm_id', max(tm.get_id_set(tu.DMs_store)))
    return tm.get_key_value_with_default('last_dm_id', default=-1)


# This next group of functions handles the actual creation of tweets based on our stored copies of The Donald's tweets
def did_donnie_say_it(what):
    """Return True if WHAT has appeared in the Trump tweets we know about, or
    False otherwise.
    """
    try:
        return (what.strip().lower() in tm.get_donnies_tweet_text().strip().lower())
    except Exception as err:
        log_it("WARNING: did_donnie_say_it() encountered error '%s'; assuming he didn't say it" % err, 2)
        return False

def did_we_say_it(what):
    """Return True if we've previously tweeted WHAT, or False otherwise."""
    try:
        return (what.strip().lower() in tm.get_our_tweet_text().strip().lower())
    except Exception as err:
        log_it("WARNING: did_we_say_it() encountered error '%s'; assuming we didn't say it" % err, 2)
        return False

def validate_tweet(the_tweet):
    """Return True if the tweet is acceptable according to whatever criteria this
    particular function decides, or False if the tweet is not acceptable.

    Currently, the function approves all tweets, unless they meet any of the
    following criteria:

        * length of tweet is not in range(20,141)
        * tweet is exactly the same as a tweet by The Donald.
        * tweet is identical to a previous tweet by this account
    """
    log_it("INFO: function validate_tweet() called", 3)
    if not len(the_tweet.strip()) in range(20, 141):
        log_it('INFO; rejecting tweet "%s" because its length is %d' % (the_tweet, len(the_tweet.strip())), 3)
        return False
    if did_donnie_say_it(the_tweet):
        log_it('INFO: rejecting tweet "%s" because The Donald has said exactly that.' % the_tweet, 2)
        return False
    if did_we_say_it(the_tweet):
        log_it('INFO: rejecting tweet "%s" because we\'ve previously said precisely that.' % the_tweet, 2)
        return False
    log_it('INFO: approving tweet "%s".' % the_tweet, 3)
    return True

def get_tweet(starts, the_mapping):
    """Produces a tweet by repeatedly calling the text generator with varying
    parameters until it just so happens that it coughs up something that
    validate_tweet() approves of.
    """
    got_tweet = False
    while not got_tweet:
        sents = random.choice(range(1, 5))
        log_it("Generating a tweet (%d sentences) ..." % sents)
        the_tweet = sg.gen_text(the_mapping, starts, markov_length=markov_length, sentences_desired=sents, paragraph_break_probability=0.1).strip()
        got_tweet = validate_tweet(the_tweet)
        log_it("    ... length is %d" % len(the_tweet))
    return the_tweet

def tweet(text, id=None, date=None):
    """Post a tweet. Also, add the tweet to the list of tweets created so far by
    the script.
    """
    log_it("Tweet is: '%s'. Posting ..." % text)
    the_status = sm.post_tweet(Trump_client, text)

    log_it("Adding that tweet to our tweet archive")
    with open(tu.tweets_store, mode='a', newline='') as archive_file:
        writer = csv.writer(archive_file, dialect='unix')
        writer.writerow([the_status.text, the_status.id, str(the_status.created_at)])
    the_lines = tm.get_donnies_tweet_text().split('\n')


# This next group of functions handles the downloading, processing, and storing of The Donald's tweets.
def get_new_tweets(screen_name=tu.target_twitter_id, oldest=-1):
    """Get those tweets newer than the tweet whose ID is specified as the OLDEST
    parameter from the account SCREEN_NAME.
    """
    # get most recent tweets (200 is maximum possible at once)
    new_tweets = the_API.user_timeline(screen_name=screen_name, count=200)
    ret = new_tweets.copy()

    oldest_tweet = ret[-1].id - 1  # save the id of the tweet before the oldest tweet

    # keep grabbing tweets until there are no tweets left
    while len(new_tweets) > 0 and oldest < new_tweets[0].id:
        log_it("getting all tweets before ID #%s" % (oldest_tweet))
        new_tweets = the_API.user_timeline(screen_name=screen_name, count=200, max_id=oldest_tweet)
        ret.extend(new_tweets)
        oldest_tweet = ret[-1].id - 1
        log_it("    ...%s tweets downloaded so far" % (len(ret)))
    tm.set_data_value('newest_tweet_id', max([t.id for t in ret]))
    return [t for t in ret if (t.id > oldest)]

def filter_tweet(tweet_text):
    """Returns True if a tweet from The Donald should be filtered (i.e., eliminated
    from the list of tweets that the script is aware of), or False if it should
    not be filtered (i.e., should remain in the list).

    Currently, just eliminates tweets with URLs and tweets that @mention any
    account other than @realDonaldTrump (i.e., when The Donald talks about, or to,
    anyone else -- we don't want this account interacting with people just because
    The Donald does. The Donald is a terrible model for appropriate behavior
    in many, many ways).

    However, there may need to be more nuanced behavior in the future.
    """
    if 't.co' in tweet_text:        # Assumption: all URLs coming from Twitter contain Twitter's redirection domain.
        return True  # At this time, the text generator doesn't deal well with input text containing URLs.
    elif '@' in tweet_text:         # Since more than one @mention can occur in a tweet ...
        mentions = list(set([w for w in tweet_text.split() if '@' in w]))  # Make a list of all unique @mentions
        if len(mentions) == 1:      # Allow The Donald to talk about himself (& not other people) without filtering those tweets out.
            return not (th.strip_leading_and_trailing_punctuation(mentions[0].strip()).strip().lower() == tu.target_twitter_id.strip().lower())
        else:               # Filter out tweets mentioning more than one person:
            return True     # by def'n, they're not just The Donald being self-aggrandizing.
    return False


def normalize(the_tweet):
    """Convert THE_TWEET into a normalized form, based on the replacements in
    SUBSTITUTION_LIST (specified below). All substitutions are applied repeatedly,
    in the order they appear in the list, until none of them produces a change.
    HTML/XML entities are also unescaped, and any necessary other transformations
    are applied.

    Currently, "other transformations" means:
        * acronyms are (hopefully) detected, and their periods replaced with one-
          dot leaders, so the Markov chain creator treats them as single words.

    THE_TWEET is a Tweepy tweet object, not a string. (This routine currently
    only deals with THE_TWEET.text, however).

    SUBSTITUTION_LIST, below, is a list of two-item lists of the form
        [[ search_item_1, replacement_item_1],
         [ search_item_2, replacement_item_2],
         [...]
        ]

    Each SEARCH_ITEM and REPLACE_ITEM is a regex passed to th.multi_replace();
    see documentation for that function for more information.
    """
    substitution_list = [['\n', ' '],                   # Newline to space
                         ['  ', ' '],                   # Two spaces to one space
#                         ['U\.S\.A\.', 'U․S․A․'],       # Periods to one-dot leaders
                         ['U\. S\. A\.', 'U․S․A․'],     # Periods to one-dot leaders, remove spaces
                         ['U\. S\.', 'U․S․'],           # Periods to one-dot leaders, remove spaces
#                         ['U\.S\.', 'U․S․'],            # Periods to one-dot leaders
#                         ['P\.M\.', 'P․M․'],            # Again
                         ['p\.m\.', 'p․m․'],            # Again
#                         ['A\.M\.', 'A․M․'],            # Again
                         ['a\.m\.', 'a․m․'],            # Again
#                         ['V\.P\.', 'V․P․'],            # Again
                         ['Mr\.', 'Mr․'],               # Again
                         ['Dr\.', 'Dr․'],               # Again
                         ['Mrs\.', 'Mrs․'],             # Again
                         ['Pres\.', 'Pres․'],           # Again
                         ['Ms\.', 'Ms․'],               # Again
                         ['Rev\.', 'Rev․'],             # Again
                         ['Sen\.', 'Sen․'],             # Again
                         ['Gov\.', 'Gov․'],             # Again
                         [' \n', '\n'],                 # Space-then-newline to newline
                         ['\.\.\.\.', '...'],               # Four periods to three periods
                         ['\.\.', '.'],                   # Two periods to one period
                         ['\.\.\.', '…'],                  # Three periods to ellipsis
                         ['…\.', '…'],                   # Ellipsis-period to ellipsis. …. may be allowable, but is unlikely for Donnie.
                         ['……', '…'],                   # Double-ellipsis to ellipsis.
                         ['… …', '…'],                  # Double-ellipsis-with-space to ellipsis
                        ]
    the_tweet.text = sg.process_acronyms(the_tweet.text)
    the_tweet.text = th.multi_replace(html.unescape(th.multi_replace(the_tweet.text, substitution_list)),substitution_list)
    return the_tweet

def massage_tweets(the_tweets):
    """Make tweets The Donald more suitable for feeding into the Markov-chain,
    generator. Part of this involves silently dropping tweets that can't
    effectively be used by the Markov chain-based generator; once this is done,
    the remaining tweets are passed through normalize() to smooth out (some of)
    their remaining rough edges.
    """
    return [normalize(t) for t in the_tweets if not filter_tweet(t.text)]

def save_tweets(the_tweets):
    """Save the text from THE_TWEETS to a CSV file, and update the stored data.
    THE_TWEETS is a list of tweepy.Tweet objects, not strings.

    See the function get_our_tweet_text() in trump_utils.py for a declaration of
    the format of the .csv file.
    """
    if len(the_tweets) == 0:  # If there are no new tweets, don't do anything
        return
    with open('%s/%s.csv' % (tu.donnies_tweets_dir, datetime.datetime.now().isoformat()), 'w', newline="") as f:
        csvwriter = csv.writer(f, dialect='unix')
        for t in the_tweets:
            csvwriter.writerow([t.text, t.id_str, t.created_at])
    tm.set_data_value('last_update_date', datetime.datetime.now())  # then, update the database of tweet-record filenames and ID numbers

def update_tweet_collection():
    """Update the tweet collection."""
    log_it("INFO: updating tweet collection")
    t = get_new_tweets(screen_name=tu.target_twitter_id, oldest=get_newest_tweet_id())
    t = massage_tweets(t)
    save_tweets(t)
    tm.export_plaintext_tweets()    # Make sure that an up-to-date export is there for applications that consume it.

def update_tweet_collection_if_necessary():
    """Once in a while, import new tweets encoding the brilliance that The Donald &
    his team have graced the world by sharing.
    """
    if tu.force_download or tm._num_tweet_files() == 0 or (datetime.datetime.now()-get_last_update_date()).days > 30 or random.random() < 0.01:
        update_tweet_collection()


# The next group of functions handles user interaction via DMs and @mentions, and handles commands from me.
def process_command(command, issuer_id):
    """Process a command coming from my own Twitter account."""
    command_parts = [c.strip().lower() for c in command.strip().split() if not c.strip().startswith('@')]
    if command_parts[0] in ['stop', 'quiet', 'silence']:
        tm.set_data_value('stopped', True)
        sm.send_DM(the_API=the_API, text='You got it, sir, halting tweets per your command.', user=issuer_id)
    elif command_parts[0] in ['start', 'verbose', 'go', 'loud', 'begin']:
        tm.set_data_value('stopped', False)
        sm.send_DM(the_API=the_API, text='Yessir, beginning tweeting again per your command.', user=issuer_id)
    elif command_parts[0] in ['update', 'refresh', 'check', 'reload', 'new']:
        update_tweet_collection()
        sm.send_DM(the_API=the_API, text='You got it, sir: tweet collection updated.', user=issuer_id)
    else:
        sm.send_DM(the_API=the_API, text="Sorry, sir. I didn't understand that.", user=issuer_id)

def handle_mention(mention):
    """Process the @mention in whatever way is appropriate."""
    log_it("INFO: Handling mention ID #%d" % mention.id)
    log_it("text is: %s" % mention.text)
    log_it("user is: @%s" % mention.user.screen_name)
    if mention.user.screen_name.strip('@').lower() == tu.programmer_twitter_id.strip('@').lower():
        tm.remember_id(tu.mentions_store, mention.id) # Force-learn it now: commands can force-terminate the script.
        tm.set_data_value('last_mention_id', max(mention.id, get_newest_mention_id()))
        process_command(mention.text, issuer_id=tu.programmer_twitter_id)
    elif mention.user.screen_name.strip('@').lower().strip() == tu.target_twitter_id:
        log_it("Oh my! The Donald is speaking! Click your jackboots together and salute!")
        sm.modified_retweet('LOL\n\n', user_id=tu.target_twitter_id, tweet_id=mention.id)
    else:
        log_it('WARNING: unhandled mention from user @%s' % mention.user.screen_name)
        log_it("the tweet is: %s" % mention.text)
    tm.remember_id(tu.mentions_store, mention.id)
    tm.set_data_value('last_mention_id', max(mention.id, get_newest_mention_id()))

def check_mentions():
    """A stub to check for any @mentions and, if necessary, reply to them."""
    for mention in [m for m in tm.get_all_mentions(the_API=the_API) if m.id > get_newest_mention_id()]:
        if not tm.seen_mention(mention.id):
            handle_mention(mention)

def handle_dm(direct_message):
    """Handle a given direct message. Currently, it just treats any DM from me as a
    command, and replies to anyone else with an explanation that it doesn't
    respond usefully to DMs.
    """
    log_it("INFO: Handling direct message ID #%d" % direct_message.id)
    log_it("direct message is:\n\n%s" % pprint.pformat(direct_message), 3)
    log_it("text is: %s" % direct_message.text)
    log_it("user is: @%s" % direct_message.sender_screen_name)
    if direct_message.sender_screen_name.lower().strip('@') == tu.programmer_twitter_id.lower().strip('@'):
        process_command(direct_message.text, issuer_id=tu.programmer_twitter_id)
    else:
        log_it("WARNING: unhandled DM detected:")
        log_it(pprint.pformat(direct_message))
        log_it("Replying with default message")
        sm.send_DM(the_API=the_API, text="Sorry, I'm a bot and don't process direct messages. If you need to reach my human minder, he's @patrick_mooney.", user=direct_message.sender_screen_name)
    tm.remember_id(tu.DMs_store, direct_message.id)
    tm.set_data_value('last_dm_id', max(direct_message.id, get_newest_dm_id()))

def check_DMs():
    """Check and handle any direct messages."""
    for dm in [dm for dm in tm.get_all_DMs(lowest_id=get_newest_dm_id(), the_API=the_API) if not tm.seen_DM(dm.id)]:
        handle_dm(dm)

def set_up():
    """Perform pre-tweeting tasks: updates the collection of stored tweets;
    checks for new @mentions and DMs.
    """
    update_tweet_collection_if_necessary()
    check_mentions()
    check_DMs()


if __name__ == '__main__':
    set_up()
    if tm.get_data_value('stopped'):
        log_it('Aborting: user data key "stopped" is set.')
        sys.exit(0)

    # @realDonaldTrump tweeted 200 times between 12/04/16 03:48 AM & 01/10/17 12:51 PM; that's approx. 5.3 tweets/day.
    # If this script is called every fifteen minutes by a cron job, that's 96 times/day
    # That works out to needing to tweet on 5.57382532% of the script's invocations.
    if tu.force_tweet or random.random() <= 0.0557382532:
        donnies_words = [][:]
        for the_file in tm.all_donnies_tweet_files():
            donnies_words += sg.word_list_from_string(tm.get_tweet_archive_text(the_file))
        starts, the_mapping = sg.buildMapping(donnies_words, markov_length=markov_length)
        the_tweet = get_tweet(starts, the_mapping)
        tweet(the_tweet)
    else:
        log_it('INFO: not tweeting because dice roll failed')
