#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("Content-Type: text/html; charset=utf-8\n\n")

import sys
sys.stderr = sys.stdout

import glob, random, re, cgi, csv, os
import trump_utils as tu

# Overwrite some values from trump_utils.py with web server locations.
tu.base_dir = '/home/public/~patrick/projects/TrumpQuiz' 
tu.data_dir = tu.base_dir
tu.data_store = ""  # '%s/TrumpTweets_data.pkl' % tu.data_dir
tu.tweets_store = ""
tu.DMs_store = ""
tu.mentions_store = ""
tu.donnies_tweets_dir = ""
tu.our_minimal_tweets = "%s/false_trump.csv" % tu.data_dir
tu.donnies_minimal_tweets = "%s/trump.csv" % tu.data_dir
tu.answer_counts = '%s/stats.csv' % tu.base_dir

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
<meta name="date" content="2017-01-27T04:16:48-0800" />
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

# Parse any CGI parameters passed by a previous invocation & write appropriate resulting text evaluating guess 
form = cgi.FieldStorage()

if 'tweet_text' in form:     # Then we're evaluating a previous quiz, and should provide feedback.
    print("""<div class="u-pull-right two-thirds column"><blockquote class="twitter-tweet" data-lang="en"><p lang="en" dir="ltr">%s</p>&mdash; (@%s) <a href="%s">%s</a></blockquote>\n<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script></div>""" % (form['tweet_text'].value, form['orig_account'].value, tu.get_tweet_url(form['orig_account'].value, form['tweet_id'].value), form['tweet_date'].value))
    if form['guess'].value == form['orig_account'].value:   # User guess was correct
        if form['guess'].value == tu.target_twitter_id:     # User correctly guessed it was The Donald
            print("""<h2>That's right.</h2>\n\n<p>Donald Trump said this <a rel="nofollow" href="%s">on Twitter</a> (%s).</p>""" % (tu.get_tweet_url(tu.target_twitter_id, form['tweet_id'].value), form['tweet_date'].value))
            tu.bump_count('trump_right')
        else:       # User correctly guessed it was algorithmic
            print("""<h2>That's right.</h2>\n\n<p><a rel="muse" href="%s">This tweet</a> was generated by an algorithm; it appeared on the <a rel="muse" href="https://twitter.com/false_trump/">@false_trump</a> account (%s). (And if this quiz ever reports a tweet from @realDonaldTrump as beloning to @false_trump, <em>that's a bug</em> and should be <a href="https://github.com/patrick-brian-mooney/make-america-sad-again/issues">reported on GitHub</a>.)</p>""" % (tu.get_tweet_url(tu.my_twitter_id, form['tweet_id'].value), form['tweet_date'].value))
            tu.bump_count('algorithm_right')
    else:       # User guess was incorrect
        if form['guess'].value == tu.target_twitter_id:     # User incorrectly guessed it was The Donald
            print("""<h2>Sorry.</h2>\n\n<p><a rel="muse" href="%s">This tweet</a> was computer-generated; it appeared on the <a rel="muse" href="https://twitter.com/false_trump/">@false_trump</a> account (%s). (And if this quiz ever reports a tweet from @realDonaldTrump as beloning to @false_trump, <em>that's a bug</em> and should be <a href="https://github.com/patrick-brian-mooney/make-america-sad-again/issues">reported on GitHub</a>.)</p>""" % (tu.get_tweet_url(tu.my_twitter_id, form['tweet_id'].value), form['tweet_date'].value))
            tu.bump_count('trump_wrong')
        else:       # User incorrectly guessed it was algorithmic
            print("""<h2>Sorry.</h2>\n\n<p>Donald Trump said this <a rel="nofollow" href="%s">on Twitter</a> (%s).</p>""" % (tu.get_tweet_url(tu.target_twitter_id, form['tweet_id'].value), form['tweet_date'].value))
            tu.bump_count('algorithm_wrong')

print("""<p>This quiz costs money to maintain. If you enjoyed it, please consider <a rel="me" href="https://flattr.com/submit/auto?user_id=patrick_mooney&url=http%3A%2F%2Fpatrickbrianmooney.nfshost.com%2F%7Epatrick%2Fprojects%2FTrumpTweets%2Findex.cgi">making a small contribution via Flattr</a>.</p>""")
if 'tweet_text' in form:
    print("""<h2 style="clear:both;">Let's try another one.</h2>""")


# OK, summarize previous stats.


print("""<p>Take a look at the quote below. There's a 50% chance that Donald Trump said it on Twitter, and a 50% chance it was generated at random by a mindless computer program. Can you tell which it is?</p>""")

# Pick a tweet and print it.
source_account, source_file = random.choice([[tu.target_twitter_id, tu.donnies_minimal_tweets], [tu.my_twitter_id, tu.our_minimal_tweets]])

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
print("""
<footer>
<p><!--This quiz has a <a rel="me" href="privacy.html">privacy policy</a> that you can read if you want. Some technical information about this quiz is <a href="technical.html">here</a>.--> The code generating this quiz and <a href="https://twitter.com/false_trump">the @false_trump Twitter account</a> is available <a rel="me" href="https://github.com/patrick-brian-mooney/make-america-sad-again/">on GitHub</a>. Photo of Donald Trump used in this page's metadata (and which shows up when it is shared via social media) is copyright by Michael Vadon; the original picture is <a href="https://commons.wikimedia.org/wiki/File:Donald_Trump_March_2015.jpg">here</a>. Blocks of text generated by this quiz itself are not copyrightable because there is no intentionality behind them that makes them creative works. Quotes by Donald Trump in the quiz are presumably copyright by Donald Trump, to the extent that there is sufficient conscious intentionality behind them for them to qualify as copyrightable creative works. Bugs should be reported <a href="https://github.com/patrick-brian-mooney/make-america-sad-again">on GitHub</a>.</p>
<p class="status vevent vcard">Short link to this quiz: <a rel="me" class="url shortlink" href="https://is.gd/trump_tweets_quiz">https://is.gd/trump_tweets_quiz</a>. <a rel="me author" class="url location" href="#">This web page</a> is copyright © 2017 by <span class="fn">Patrick Mooney</span>. <abbr class="summary description" title="'Did Donnie Say It?' last updated">Last update to this HTML file</abbr>: <abbr class="dtstart" title="2017-01-19">19 January 2017</abbr>.</p>
</footer>\n</div></body>\n</html>""")
