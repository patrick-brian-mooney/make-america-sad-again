#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Part of Patrick Mooney's TrumpTweets project. This file holds utility code
for maintaining the state of the project as a whole.
"""


import pickle, glob, csv, random

from patrick_logger import log_it

import trump_utils as tu


# Miscellaneous convenience functions
def _num_tweet_files():
    """Convenience function to return the number of files in which The Donald's
    tweets are stored.
    """
    return len(glob.glob('%s/*csv' % tu.donnies_tweets_dir))


# This next group of functions handles storing and retrieving basic program operation parameters (persistent globals).
# This is actually an inefficient way to do this, but it'll work for the simple tasks the tweeting script needs.
# Note that lists of already-processed DMs and @mentions are stored using a similar but separate mechanism.
def _get_data_store():
    """Private function to get the entire stored data dictionary. If the data
    storage dictionary cannot be read, create a new dictionary with default
    values.
    """
    try:
        with open(tu.data_store, 'rb') as the_data_file:
            return pickle.load(the_data_file)
    except Exception:
        log_it('WARNING: Data store does not exist or cannot be read; creating new data store ...')
        the_data = {'purpose': 'data store for the TrumpTweets project at @false_trump',
                    'program author': 'Patrick Mooney',
                    'script URL': 'https://github.com/patrick-brian-mooney/make-america-sad-again',
                    'author twitter ID': '@patrick_mooney',
                    }
        with open(tu.data_store, 'wb') as the_data_file:
            pickle.dump(the_data, the_data_file)
        return the_data

def set_data_value(keyname, value):
    """Store a VALUE, by KEYNAME, in the persistent data store. This data store is
    read from disk, modified, and immediately written back to disk. This is a
    naive function that doesn't worry about multiple simultaneous attempts to
    access the store: there should never be any. (tweet_like_trump.py should be
    the only process accessing the file, and there should only be one
    invocation running at a time.)
    """
    the_data = _get_data_store()
    the_data[keyname] = value
    with open(tu.data_store, 'wb') as the_data_file:
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

def get_key_value_with_default(key_name, default=None):
    """Try to get a key value from the data store. If that fails, return the
    default value, instead, and create that key in the data store with the
    specified default value.
    """
    try:
        ret = get_data_value(key_name)
        if ret == None and default is not None:  # If necessary, set the default value.
            set_data_value(key_name, default)
            ret = default
        return ret
    except Exception as err:
        log_it('WARNING: get_key_value_with_default() encountered exception "%s"; returning default value "%s"' % (err, default), 1)
        return default


# This next group of functions handles remembering DMs and @mentions that have been seen (and dealt with) previously.
def get_id_set(which_store):
    """Unpickles and returns a set of ID numbers stored in the file WHICH_STORE.
    Errors in this routine should be caught by the calling function.
    """
    with open(which_store, 'rb') as msg_file:
        return pickle.load(msg_file)

def _store_id_set(which_store, the_set):
    """Stuff the set of seen-message IDs back into the file WHICH_STORE."""
    with open(which_store, 'wb') as msg_file:
        pickle.dump(the_set, msg_file)

def remember_id(which_store, id_num):
    """Add ID_NUM to the set of ID numbers of seen messages stored in WHICH_STORE."""
    the_set = get_id_set(which_store)
    the_set |= {id_num}
    _store_id_set(which_store, the_set)

def _seen_message(message_store, message_id):
    """Return True if the id MESSAGE_ID is in the MESSAGE_STORE data set, or
    False otherwise. Each MESSAGE_STORE file is a pickled set of IDs of messages
    already seen by the script.
    """
    try:
        return message_id in get_id_set(message_store)
    except Exception:  # If we can't verify we haven't seen it, ignore it. Don't bother people due to technical errors on our end.
        log_it("WARNING: data store '%s' doesn't exist or is unreadable; creating empty store ... " % message_store, 2)
        with open(message_store, 'wb') as msg_file:
            pickle.dump(msg_file, set([]))
        return None  # signal that something went wrong, and calling function will have to deal with it.

def _get_all_messages(source):
    """Get the set of all messages from the specified SOURCE, ever (or, at least as
    far back as the Twitter API will let us go).
    """
    ret = [][:]
    got_some = False
    while not ret and not got_some:
        new_msgs = [m for m in source()]
        got_some = True
        for item in new_msgs:
            if item not in ret:
                ret += [item]
    return ret

def get_all_DMs(the_API, lowest_id=-1):
    """Get a list of all DMs, ever; or, all DMs after the optional
    LOWEST_ID parameter.

	Needs a Tweepy API object, the_API.
    """
    return [dm for dm in _get_all_messages(lambda: the_API.direct_messages(count=100, full_text=True, since_id=lowest_id))]

def get_all_mentions(the_API):
    """Get a list of all @mentions, ever. Needs a Tweepy API object, THE_API"""
    return [m for m in _get_all_messages(lambda: the_API.mentions_timeline(count=100))]

def _learn_all_DMs():
    """Get a list of all the DMs that have ever been sent, and add them to the list
    of DMs we've ever seen. This only happens automatically if the DM store is
    recreated, on the theory that we shouldn't bother people by responding to
    DMs that have already been responded to just because some technical error on
    our end has caused the DM store to become unreadable.
    """
    log_it("INFO: _learn_all_DMs() called to recreate list")
    _store_id_set(DMs_store, {dm.id for dm in get_all_DMs()})

def _learn_all_mentions():
    """Get a list of all @mentions that have ever been sent, and add them to the
    set of @mentions we've ever seen. This only happens automatically under the
    same circumstances and for the same reasons as with _learn_all_DMs(), above.
    """
    log_it("INFO: _learn_all_mentions() called to recreate list")
    _store_id_set(tu.mentions_store, {m.id for m in get_all_mentions()})

def seen_DM(message_id):
    """Return True if the DM has been seen before, False otherwise. If the data store
    of seen DMs does not exist, it's created, and all DMs ever sent are treated
    as seen.
    """
    ret = _seen_message(tu.DMs_store, message_id)
    if ret is None:
        _learn_all_DMs()
        ret = True
    return ret

def seen_mention(message_id):
    """Return True if we have seen and processed the @mention before, or False if
    it's new to us. If the data store of seen @mentions does not exist, it's
    created, and all @mentions ever sent are remembered and assumed to have
    been processed already: we don't want to bother people by interacting with
    them again for a @mention we've already responded to.
    """
    ret = _seen_message(tu.mentions_store, message_id)
    if ret is None:
        _learn_all_mentions()
        ret = True
    return ret

# This next group of functions deals with stored tweet files.
# These files are .csv files with three columns. Each row has the structure:
#       [ tweet text, tweet ID, tweet date ]
def all_donnies_tweet_files():
    """Convenience function to return a list of all files The Donald's tweets are
    stored in.

    :return: a list of these files.
    """
    return sorted(glob.glob("%s/*csv" % tu.donnies_tweets_dir))

def get_tweet_archive_text(archive_file):
    """Returns the full text, and nothing but the text, of all tweets stored in
    a tweet archive .csv file, which stores the text of the tweets in the first
    column of the file.

    :return: a string containing the archive of all of our tweets.
    """
    with open(archive_file, newline='') as csvfile:
        csvreader =     csv.reader(csvfile, dialect='unix')
        return '\n'.join([row[0] for row in csvreader])

def get_our_tweet_text():
    """ Returns the full text of all tweets this script has created and stored.

    :return: a string containing the archive of all of our tweets.
    """
    return get_tweet_archive_text(tu.tweets_store)

def get_donnies_tweet_text():
    """Returns the full text of all of The Donald's tweets that this script is
    aware of.

    :return: a string containing the text of all such tweets.
    """
    ret = ""
    for which_file in all_donnies_tweet_files():
        ret += get_tweet_archive_text(which_file)
    return ret


# These next few functions handle exporting a randomly selected group of tweets for the web quiz. Running these functions (manually) from
# time to time will help keep the web quiz from repeating the same questions too much.
def save_tweets(tweets, archive_file):
    """Save the tweets in TWEETS to ARCHIVE_FILE.
    TWEETS is a list of [text, ID, date] lists.
    ARCHIVE_FILE is the filename of the .csv file to create or overwrite.
    """
    with open(archive_file, 'w', newline="") as f:
        csvwriter = csv.writer(f, dialect='unix')
        for t in tweets:
            csvwriter.writerow(t)

def _get_all_exact_tweets(archive_file):
    """Get all tweets stored in the .csv file specified by STORE, provided that
    they have attributed ID and timestamp attributes. These tweets are "exact"
    tweets (a bit of a misnomer because they have had some punctuation
    processing and other minor tweaks), i.e. they can be sourced to a single
    individual tweet by The Donald that is not part of a larger (ellipsis-
    delimited) tweet-spanning statement.

    RETURNS a list of lists of strings: [ tweet text, tweet ID, tweet date ]
    """
    with open(archive_file, newline='') as csvfile:
        csvreader = csv.reader(csvfile, dialect='unix')
        return [item for item in csvreader if item[1] and item[2]]  # Filter out empty IDs and empty timestamps

def _get_our_exact_tweets():
    """Returns a list -- [tweet text, tweet ID, tweet date] -- of all our tweets."""
    return _get_all_exact_tweets(tu.tweets_store)

def _get_donnies_exact_tweets():
    """Returns a list, as with get_all_our_tweets(), of all of Donnie's tweets."""
    ret = [][:]
    for the_archive in all_donnies_tweet_files():
        ret.extend(_get_all_exact_tweets(the_archive))
    return ret

def select_new_tweets(num_selected=200):
    """Pick NUM_SELECTED new tweets from each tweet store at random, and save those
    tweets to the appropriate places for the web quiz to pick them up. This
    function is never called automatically; it's just for maintenance work.
    """
    save_tweets(random.sample(_get_our_exact_tweets(), num_selected), tu.our_minimal_tweets)
    save_tweets(random.sample(_get_donnies_exact_tweets(), num_selected), tu.donnies_minimal_tweets)


# These next two utility functions handle exporting text-only versions of the tweet archive files for consumption by other applications.
# For instance, starting 20 Jan 2017, they will be a component of my *Ulysses Redux* blog, under the title "Donnie #Stomps thru Dublin"
def _plaintext_export(filename, getter):
    """Export all of The Donald's stored tweets into a single plaintext file to be
    consumed by other applications.
    """
    with open(filename, 'w') as export_file:
        export_file.write(getter())

def export_plaintext_tweets():
    """Produce plaintext versions of the tweet stores, so they
    """
    _plaintext_export(tu.donnie_plaintext_tweets, get_donnies_tweet_text)
    _plaintext_export(tu.our_plaintext_tweets, get_our_tweet_text)

if __name__ == "__main__":
    pass
