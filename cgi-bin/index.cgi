#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("Content-Type: text/html; charset=utf-8\n\n")

import sys
sys.stderr = sys.stdout

import glob, random, re, cgi, csv, os
import trump_utils as tu

# Overwrite some values from trump_utils.py with web server locations.
tu.base_dir = '/home/public/~patrick/projects/TrumpQuiz' # '/~patrick/projects/TrumpQuiz'
tu.data_dir = tu.base_dir
tu.data_store = '%s/TrumpTweets_data.pkl' % tu.data_dir
tu.tweets_store = ""
tu.DMs_store = ""
tu.mentions_store = ""
tu.donnies_tweets_dir = ""
tu.our_minimal_tweets = "%s/false_trump.csv" % tu.data_dir
tu.donnies_minimal_tweets = "%s/trump.csv" % tu.data_dir

debugging = False


print("""<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<link rel="stylesheet" type="text/css" href="http://patrickbrianmooney.nfshost.com/~patrick/css/skeleton-normalize.css" />
<link rel="stylesheet" type="text/css" href="http://patrickbrianmooney.nfshost.com/~patrick/css/skeleton.css" />
<link rel="stylesheet" type="text/css" href="http://patrickbrianmooney.nfshost.com/~patrick/css/content-skel.css" />
<link rel="stylesheet" type="text/css" href="http://patrickbrianmooney.nfshost.com/~patrick/css/pullquotes.css" />
<link rel="pgpkey" type="application/pgp-keys" href="/~patrick/505AB18E-public.asc" />
<link rel="author" href="http://plus.google.com/109251121115002208129?rel=author" />
<link rel="sitemap" href="/sitemap.xml" />
<link rel="home" href="/~patrick/" title="Home page" />
<link rel="meta" type="application/rdf+xml" title="FOAF" href="/~patrick/foaf.rdf" />
<meta name="foaf:maker" content="foaf:mbox_sha1sum '48a3091d919c5e75a5b21d2f18164eb4d38ef2cd'" />
<link rel="profile" href="http://microformats.org/profile/hcalendar" />
<link rel="profile" href="http://gmpg.org/xfn/11" />
<link rel="icon" type="image/x-icon" href="/~patrick/icons/favicon.ico" />
<title>Did Donnie Say It?</title>
<meta name="generator" content="Bluefish 2.2.6" />
<meta name="author" content="Patrick Mooney" />
<meta name="dcterms.rights" content="Copyright © 2017 Patrick Mooney" />
<meta name="description" content="Did Donald Trump say it on Twitter? Or was it a mindless robot that studies Donald Trump?" />
<meta name="rating" content="general" />
<meta name="revisit-after" content="3 days" />
<meta name="date" content="2017-01-19T03:15:28-0800" />
<meta property="fb:admins" content="100006098197123" />
<meta property="og:title" content="Did Donnie Say It?" />
<meta property="og:type" content="website" />
<meta property="og:url" content="http://patrickbrianmooney.nfshost.com/~patrick/projects/TrumpQuiz/" />
<meta property="og:image" content="https://upload.wikimedia.org/wikipedia/commons/a/a7/Donald_Trump_March_2015.jpg" />
<meta property="og:description" content="Did Donald Trump say it on Twitter? Or was it a mindless robot that studies Donald Trump?" />
<meta name="twitter:card" content="summary" />
<meta name="twitter:site" content="@false_trump" />
<meta name="twitter:creator" content="@patrick_mooney" />
<meta name="twitter:title" content="Did Donnie Say It?" />
<meta name="twitter:description" content="Did Donald Trump say it on Twitter? Or was it a mindless robot that studies Donald Trump?" />
<meta name="twitter:image:src" content="https://upload.wikimedia.org/wikipedia/commons/a/a7/Donald_Trump_March_2015.jpg" />
</head>

<body><div class="container">
<script type="text/javascript" src="/~patrick/nav.js"></script>
<noscript>
  <p class="simpleNav"><a rel="me home" href="index.html">Go home</a></p>
  <p class="simpleNav">If you had JavaScript turned on, you'd have more navigation options.</p>
</noscript>

<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-37778547-1']);
  _gaq.push(['_setDomainName', 'nfshost.com']);
  _gaq.push(['_setAllowLinker', true]);
  _gaq.push(['_trackPageview']);

  (function() {
var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script>
<h1>Did Donnie Say It?</h1>""")

# Parse any CGI parameters passed by a previous invocation, write appropriate results
form = cgi.FieldStorage()

if debugging:
    if form: print(cgi.print_form(form))


if 'tweet_text' in form:     # Then we're evaluating a previous quiz, and should provide feedback.
    print("""<div class="u-pull-right two-thirds column"><p class="quote-bubble">%s</p></div>""" % form['tweet_text'].value)
    if form['guess'].value == form['orig_account'].value:   # User guess was correct
        if form['guess'].value == tu.target_twitter_id:     # User correctly guessed it was The Donald
            print("""<h2>That's right.</h2>\n\n<p>Donald Trump said this <a rel="nofollow" href="%s">on Twitter</a> (%s).</p>""" % (tu.get_tweet_url(tu.target_twitter_id, form['tweet_id'].value), form['tweet_date'].value))
        else:       # User correctly guessed it was algorithmic
            print("""<h2>That's right.</h2>\n\n<p><a rel="muse" href="%s">This tweet</a> was generated by an algorithm; it appeared on the <a rel="muse" href="https://twitter.com/false_trump/">@false_trump</a> account (%s).</p>""" % (tu.get_tweet_url(tu.my_twitter_id, form['tweet_id'].value), form['tweet_date'].value))
    else:       # User guess was incorrect
        if form['guess'].value == tu.target_twitter_id:     # User incorrectly guessed it was The Donald
            print("""<h2>Sorry.</h2>\n\n<p><a rel="muse" href="%s">This tweet</a> was computer-generated; it appeared on the <a rel="muse" href="https://twitter.com/false_trump/">@false_trump</a> account (%s).</p>""" % (tu.get_tweet_url(tu.my_twitter_id, form['tweet_id'].value), form['tweet_date'].value))
        else:       # User incorrectly guessed it was algorithmic
            print("""<h2>Sorry.</h2>\n\n<p>Donald Trump said this <a rel="nofollow" href="%s">on Twitter</a> (%s).</p>""" % (tu.get_tweet_url(tu.target_twitter_id, form['tweet_id'].value), form['tweet_date'].value))

"""
    if form['quoteloc'].value == 'None' and form['who'].value == 'algorithm':
        print("<h2>That's right.</h2>\n\n<p>This <strong>is</strong> gibberish, but it's not (exactly) the kind of gibberish that Sarah Palin spouts off when she speaks. Good eye!</p>")
        bump_count('algorithm_right')
    elif form['quoteloc'].value != 'None' and form['who'].value == 'sarah':
        desc, location = get_speech_info(form['quoteloc'].value)
        print("<h2>That's right.</h2>\n\n<p>Sarah Palin <strong>actually said this</strong> %s. You can read the full text from which this quote is taken <a rel="nofollow" href="%s">here</a>." % (desc, location))
        bump_count('sarah_right')
    elif form['quoteloc'].value != 'None' and form['who'].value == 'algorithm':
        desc, location = get_speech_info(form['quoteloc'].value)
        print("<h2>Sorry.</h2>\n\n<p>You might <strong>think</strong> that this disassociative text was generated by a computer trying to sound like a person, but <strong>Sarah Palin actually said this</strong> %s. You can read the text from which this was taken <a rel="nofollow" href="%s">here</a>." % (desc, location))
        bump_count('algorithm_wrong')
    elif form['quoteloc'].value == 'None' and form['who'].value == 'sarah':
        print("<h2>Sorry.</h2>\n\n<p>That might <strong>sound like</strong> the kind of crazy, disassociative shit that Sarah Palin would say, but in fact it was generated by a computer algorithm.")
        bump_count('sarah_wrong')
    else: print("<h2>Something went wrong.</h2><p>I wasn't able to evaluate your previous answer. Sorry about that.</p>")
"""
print("""<p>This quiz costs money to maintain. If you enjoyed it, please consider <a rel="me" href="https://flattr.com/submit/auto?user_id=patrick_mooney&url=http%3A%2F%2Fpatrickbrianmooney.nfshost.com%2F%7Epatrick%2Fprojects%2Fsarah-palin%2Findex.cgi">making a small contribution via Flattr</a>.</p>""")
print("""<h2 style="clear:both;">Let's try another one.</h2>""")


# OK, summarize previous stats.
"""tdata = get_stats_dictionary()

print("<p><a rel="me" href="index.cgi">This quiz</a> has been taken %d times; users have correctly identified the source of quotes %0.2f %% of the time. <a rel="me" href="stats.cgi">More stats</a>.</p>\n"  % (sum(tdata.values()), 100 * ((tdata['sarah_right'] + tdata['algorithm_right']) / sum(tdata.values()))))
"""

print("""<p>Take a look at the quote below. There's a 50% chance that Donald Trump said it on Twitter, and a 50% chance it was generated at random by a mindless computer program. Can you tell which it is?</p>""")

# Pick a tweet and print it.
source_account, source_file = random.choice([[tu.target_twitter_id, tu.donnies_minimal_tweets], [tu.my_twitter_id, tu.our_minimal_tweets]])

if debugging:
    print("<p><strong>DEBUGGING:</strong> <code>source_account</code> is: %s</p>" % source_account)
    print("<p><strong>DEBUGGING:</strong> <code>source_file</code> is: %s</p>" % source_file)

tweet = tu.get_random_tweet(source_file)
print('<p class="speech-bubble">%s</p>' % tweet['text'])
print("""<h2>Who said it?</h2>
<form method="POST" action="index.cgi">""")

# Randomly mix up radio button order and which is selected by default to avoid introducing bias.
which_order = random.randint(1,4)
if which_order == 0: print('<input type="radio" checked="checked" name="guess" value="realDonaldTrump"> The real Donald Trump<br />\n<input type="radio" name="guess" value="false_trump"> A mindless program<br />\n')
elif which_order == 1: print('<input type="radio" name="guess" value="realDonaldTrump"> The real Donald Trump<br />\n<input checked="checked" type="radio" name="guess" value="false_trump"> A mindless program<br />\n')
elif which_order == 2: print('<input type="radio" name="guess" value="false_trump"> A mindless program<br />\n<input type="radio" checked="checked" name="guess" value="realDonaldTrump"> The real Donald Trump<br />\n')
else: print('<input type="radio" checked="checked" name="guess" value="false_trump"> A mindless program<br />\n<input type="radio" name="guess" value="realDonaldTrump"> The real Donald Trump<br />\n')

# OK, encode the hidden data.
print("""
<input type="hidden" name="tweet_text" value="%s">
<input type="hidden" name="tweet_id" value="%s">
<input type="hidden" name="tweet_date" value="%s">
<input type="hidden" name="orig_account" value="%s">
<input type="submit" value="I know!" class="button-primary">
</form>""" % (cgi.escape(tweet['text']), cgi.escape(tweet['id']), cgi.escape(tweet['date']), cgi.escape(source_account)))

# Print the footer
# print("""
# <footer>
# <p>This quiz has a <a rel="me" href="privacy.html">privacy policy</a> that you can read if you want. The list of speeches and other texts used in this quiz is <a rel="me" href="speech-list.cgi">here</a>. Some technical information about this quiz is <a href="technical.html">here</a>. The code generating the quiz and the speech texts that the quiz is based on are available <a rel="me" href="https://github.com/patrick-brian-mooney/sarah-palin-quotes">here</a>. Photo of Sarah Palin used in this page's metadata (and which shows up when it is shared via social media) is copyright by Wikipedia user Therealbs2002; the original picture is <a href="https://commons.wikimedia.org/wiki/File:SarahPalinElon.jpg">here</a>. Blocks of text generated by this quiz itself are not copyrightable because there is no intentionality behind them that makes them creative works. Quotes by Sarah Palin in the quiz are presumably copyright by Sarah Palin, to the extent that there is sufficient conscious intentionality behind them for them to qualify as copyrightable creative works. If you know of a reliable transcript of a Sarah Palin speech, interview, statement, or other relevant text that this site should use, please reach me <a rel="me" href="https://gnusocial.no/p">on GNUsocial</a> or <a rel="me" href="http://twitter.com/patrick_mooney">on Twitter</a> or <a rel="me" href="/~patrick/personal.html#other-web">elsewhere online</a>.</p>
# <p class="status vevent vcard">Short link to this quiz: <a rel="me" class="url" href="http://is.gd/sarah_palin_quiz">http://is.gd/sarah_palin_quiz</a>. <a rel="me author" class="url location" href="#">This web page</a> is copyright © 2016 by <span class="fn">Patrick Mooney</span>. <abbr class="summary description" title="'Sarah Palin Quote, or Random Algorithmic Gibberish?' last updated">Last update to this HTML file</abbr>: <abbr class="dtstart" title="2016-02-10">10 February 2016</abbr>.</p>
# </footer>""")
print("</div></body>\n</html>")
