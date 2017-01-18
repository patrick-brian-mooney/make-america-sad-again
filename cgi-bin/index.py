#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("Content-Type: text/html; charset=utf-8\n\n")

import sys
sys.stderr = sys.stdout

import glob, random, re, cgi, csv, os
from sentence_generator import *            # https://github.com/patrick-brian-mooney/markov-sentence-generator

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
<meta name="date" content="2017-01-18T02:08:48-0800" />
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

if 'quote' in form:     # Then we're evaluating a previous quiz, and should provide feedback.
    print("""<div class="u-pull-right two-thirds column"><p class="quote-bubble">%s</p></div>""" % form['quote'].value)
    if form['quoteloc'].value == 'None' and form['who'].value == 'algorithm':
        print("""<h2>That's right.</h2>\n\n<p>This <strong>is</strong> gibberish, but it's not (exactly) the kind of gibberish that Sarah Palin spouts off when she speaks. Good eye!</p>""")
        bump_count('algorithm_right')
    elif form['quoteloc'].value != 'None' and form['who'].value == 'sarah':
        desc, location = get_speech_info(form['quoteloc'].value)
        print("""<h2>That's right.</h2>\n\n<p>Sarah Palin <strong>actually said this</strong> %s. You can read the full text from which this quote is taken <a rel="nofollow" href="%s">here</a>.""" % (desc, location))
        bump_count('sarah_right')
    elif form['quoteloc'].value != 'None' and form['who'].value == 'algorithm':
        desc, location = get_speech_info(form['quoteloc'].value)
        print("""<h2>Sorry.</h2>\n\n<p>You might <strong>think</strong> that this disassociative text was generated by a computer trying to sound like a person, but <strong>Sarah Palin actually said this</strong> %s. You can read the text from which this was taken <a rel="nofollow" href="%s">here</a>.""" % (desc, location))
        bump_count('algorithm_wrong')
    elif form['quoteloc'].value == 'None' and form['who'].value == 'sarah':
        print("""<h2>Sorry.</h2>\n\n<p>That might <strong>sound like</strong> the kind of crazy, disassociative shit that Sarah Palin would say, but in fact it was generated by a computer algorithm.""")
        bump_count('sarah_wrong')
    else: print("<h2>Something went wrong.</h2><p>I wasn't able to evaluate your previous answer. Sorry about that.</p>")
    print("""<p>This quiz costs money to maintain. If you enjoyed it, please consider <a rel="me" href="https://flattr.com/submit/auto?user_id=patrick_mooney&url=http%3A%2F%2Fpatrickbrianmooney.nfshost.com%2F%7Epatrick%2Fprojects%2Fsarah-palin%2Findex.cgi">making a small contribution via Flattr</a>.</p>""")
    print("""<h2 style="clear:both;">Let's try another one.</h2>""")


if debugging:
    try:
        the_html = "<h3>debugging</h3><p>the submitted form was:</p>" + "<dl><dt>who:</dt><dd>%s</dd><dt>quoteloc</dt><dd>%s</dd><dt>quote</dt><dd>%s</dd></dl>" % (form['who'].value, form['quoteloc'].value, form['quote'].value)
        print(the_html)
        print(" 'quoteloc' in form?  %s" % ('quoteloc' in form))
    except KeyError:
        pass

# OK, summarize previous stats.
"""tdata = get_stats_dictionary()

print("<p><a rel="me" href="index.cgi">This quiz</a> has been taken %d times; users have correctly identified the source of quotes %0.2f %% of the time. <a rel="me" href="stats.cgi">More stats</a>.</p>\n"  % (sum(tdata.values()), 100 * ((tdata['sarah_right'] + tdata['algorithm_right']) / sum(tdata.values()))))
"""

print("""<p>There's a 50% chance that Donald Trump said the quote below, and a 50% chance it what automatically generated by a mindless computer program operating at random. Can you tell which it is?</p>""")

# OK, generate the random text.
"""num_sentences = random.randint(2,4)

if random.random() >= 0.5:      # Generate some new Sarah Palin–style gibberish
    the_list = []
    markov_length, the_starts, the_mapping = read_chains('speeches/3chains.dat')
    the_quote = gen_text(the_mapping, the_starts, markov_length=markov_length, sentences_desired=num_sentences, paragraph_break_probability=0)
    quote_loc = 'None'
else:                           # Quote some gibberish that Sarah Palin herself generated.
    quote_loc = random.choice(glob.glob('speeches/*txt'))
    with open(quote_loc) as the_file:
        the_lines = the_file.readlines()
        all_sentences = re.split('(?<=[.!?]) +', ' '.join(the_lines))
        first_sentence = random.choice(range(len(all_sentences) - num_sentences))
        the_quote = ' '.join(all_sentences[first_sentence : first_sentence + num_sentences])
the_quote = the_quote.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')  # Escape HTML entities
print('<p class="speech-bubble">%s</p>' % the_quote)
"""

print("""<form method="POST" action="index.cgi">
<h2>Who said it?</h2>""")

# Randomly mix up radio button order and which is selected by default to avoid introducing bias.
which_order = random.randint(1,4)
if which_order == 0: print('<input type="radio" name="who" checked="checked" value="@realDonaldTrump"> The real Donald Trump<br />\n<input type="radio" name="who" value="@false_trump"> A mindless program<br />\n')
elif which_order == 1: print('<input type="radio" name="who" value="@realDonaldTrump"> The real Donald Trump<br />\n<input type="radio" name="who" checked="checked" value="@false_trump"> A mindless program<br />\n')
elif which_order == 2: print('<input type="radio" name="who" value="@false_trump"> A mindless program<br />\n<input type="radio" name="who" checked="checked" value="@realDonaldTrump"> The real Donald Trump<br />\n')
else: print('<input type="radio" name="who" checked="checked" value="@false_trump"> A mindless program<br />\n<input type="radio" name="who" value="@realDonaldTrump"> The real Donald Trump<br />\n')

# OK, encode the hidden data.
# print("""<input type="hidden" name="quote" value="%s">
# <input type="hidden" name="quoteloc" value="%s">
# <input type="submit" value="I know!" class="button-primary">
# </form>""" % (cgi.escape(the_quote), cgi.escape(quote_loc)))

# Print the footer
# print("""
# <footer>
# <p>This quiz has a <a rel="me" href="privacy.html">privacy policy</a> that you can read if you want. The list of speeches and other texts used in this quiz is <a rel="me" href="speech-list.cgi">here</a>. Some technical information about this quiz is <a href="technical.html">here</a>. The code generating the quiz and the speech texts that the quiz is based on are available <a rel="me" href="https://github.com/patrick-brian-mooney/sarah-palin-quotes">here</a>. Photo of Sarah Palin used in this page's metadata (and which shows up when it is shared via social media) is copyright by Wikipedia user Therealbs2002; the original picture is <a href="https://commons.wikimedia.org/wiki/File:SarahPalinElon.jpg">here</a>. Blocks of text generated by this quiz itself are not copyrightable because there is no intentionality behind them that makes them creative works. Quotes by Sarah Palin in the quiz are presumably copyright by Sarah Palin, to the extent that there is sufficient conscious intentionality behind them for them to qualify as copyrightable creative works. If you know of a reliable transcript of a Sarah Palin speech, interview, statement, or other relevant text that this site should use, please reach me <a rel="me" href="https://gnusocial.no/p">on GNUsocial</a> or <a rel="me" href="http://twitter.com/patrick_mooney">on Twitter</a> or <a rel="me" href="/~patrick/personal.html#other-web">elsewhere online</a>.</p>
# <p class="status vevent vcard">Short link to this quiz: <a rel="me" class="url" href="http://is.gd/sarah_palin_quiz">http://is.gd/sarah_palin_quiz</a>. <a rel="me author" class="url location" href="#">This web page</a> is copyright © 2016 by <span class="fn">Patrick Mooney</span>. <abbr class="summary description" title="'Sarah Palin Quote, or Random Algorithmic Gibberish?' last updated">Last update to this HTML file</abbr>: <abbr class="dtstart" title="2016-02-10">10 February 2016</abbr>.</p>
# </footer>
# </div></body>
# </html>""")
