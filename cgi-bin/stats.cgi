#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("Content-Type: text/html; charset=utf-8\n\n")

import sys
sys.stderr = sys.stdout

import trump_utils as tu

print("""<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<link rel="stylesheet" type="text/css" href="http://patrickbrianmooney.nfshost.com/~patrick/css/skeleton-normalize.css" />
<link rel="stylesheet" type="text/css" href="http://patrickbrianmooney.nfshost.com/~patrick/css/skeleton.css" />
<link rel="stylesheet" type="text/css" href="http://patrickbrianmooney.nfshost.com/~patrick/css/content-skel.css" />
<link rel="pgpkey" type="application/pgp-keys" href="/~patrick/505AB18E-public.asc" />
<link rel="author" href="http://plus.google.com/109251121115002208129?rel=author" />
<link rel="sitemap" href="/sitemap.xml" />
<link rel="home" href="/~patrick/" title="Home page" />
<link rel="meta" type="application/rdf+xml" title="FOAF" href="/~patrick/foaf.rdf" />
<meta name="foaf:maker" content="foaf:mbox_sha1sum '48a3091d919c5e75a5b21d2f18164eb4d38ef2cd'" />
<link rel="profile" href="http://microformats.org/profile/hcalendar" />
<link rel="profile" href="http://gmpg.org/xfn/11" />
<link rel="icon" type="image/x-icon" href="/~patrick/icons/favicon.ico" />
<title>Stats for Did Donnie Say It?</title>
<meta name="generator" content="Bluefish 2.2.6" />
<meta name="author" content="Patrick Mooney" />
<meta name="dcterms.rights" content="Copyright © 2016&ndash;17 Patrick Mooney" />
<meta name="description" content="Can Donald Trump pass a crowdsourced Turing test?" />
<meta name="rating" content="general" />
<meta name="revisit-after" content="3 days" />
<meta name="date" content="2017-01-27T13:04:10-0800" />
<meta property="fb:admins" content="100006098197123" />
<meta property="og:title" content="Stats for Did Donnie Say It?" />
<meta property="og:type" content="website" />
<meta property="og:url" content="http://patrickbrianmooney.nfshost.com/~patrick/projects/TrumpQuiz/" />
<meta property="og:image" content="https://upload.wikimedia.org/wikipedia/commons/a/a7/Donald_Trump_March_2015.jpg" />
<meta property="og:description" content="Can Donald Trump pass a crowdsourced Turing test?" />
<meta name="twitter:card" content="summary" />
<meta name="twitter:site" content="@false_trump" />
<meta name="twitter:creator" content="@patrick_mooney" />
<meta name="twitter:title" content="Stats for Did Donnie Say It?" />
<meta name="twitter:description" content="Can Donald Trump pass a crowdsourced Turing test?" />
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
<h1>Stats for Did Donnie Say It?</h1>""")

tdata = tu.get_stats_dictionary()

times_taken = sum(tdata.values())

print("""<p><a rel="me" href="index.cgi">This quiz</a> has been taken %d times; users have correctly identified the source of quotes %0.2f %% of the time. Here are the totals:</p> 
""" % (times_taken, 100 * ((tdata['trump_right'] + tdata['algorithm_right']) / times_taken)))

print("""<div>
  <table>
    <tr><th>&nbsp;</th><th>&nbsp;</th><th colspan="2" scope="colgroup">User Guess</th></tr>
    <tr><th>&nbsp;</th><th>&nbsp;</th><th scope="col">Donald Trump</th><th scope="col">Algorithm</th><th scope="col">Totals</th></tr>
    <tr><th rowspan="2" scope="rowgroup">Actual Source</th><th scope="row">Donald Trump</th><td>%d (%0.2f%%)</td><td>%d (%0.2f%%)</td><td><span class="line-header">%d (%0.2f%%)</span></td></tr>
""" % (tdata['trump_right'], 100 * (tdata['trump_right'] / times_taken), tdata['algorithm_wrong'], 100 * (tdata['algorithm_wrong'] / times_taken), tdata['trump_right'] + tdata['algorithm_wrong'], 100 * ((tdata['trump_right'] + tdata['algorithm_wrong']) / times_taken)))

print("""    <tr><th scope="row">Algorithm</th><td>%d (%0.2f%%)</td><td>%d (%0.2f%%)</td><td><span class="line-header">%d (%0.2f%%)</span></td></tr>
""" % (tdata['trump_wrong'], 100 * (tdata['trump_wrong'] / times_taken), tdata['algorithm_right'], 100 * (tdata['algorithm_right'] / times_taken), tdata['trump_wrong'] + tdata['algorithm_right'], 100 * ((tdata['trump_wrong'] + tdata['algorithm_right']) / times_taken)))

print("""    <tr><td>&nbsp;</td><th scope="row">Totals</th><td><span class="line-header">%d (%0.2f%%)</span></td><td><span class="line-header">%d (%0.2f%%)</span></td><td>&nbsp;</td></tr>
  </table>
</div>
""" % (tdata['trump_wrong'] + tdata['trump_right'], 100 * ((tdata['trump_wrong'] + tdata['trump_right']) / times_taken), tdata['algorithm_wrong'] + tdata['algorithm_right'], 100 * ((tdata['algorithm_wrong'] + tdata['algorithm_right']) / times_taken)))

print("""

<p>You can download the raw data <a rel="me" href="stats.csv">here</a>, if you'd like.</p>

<p><a rel="me" href="index.cgi">Back to <q>Did Donnie Say It?</q></a></p>

<footer class="status vevent">
<p>This quiz has a <a rel="me" href="privacy.html">privacy policy</a> that you can read if you want. <a rel="me author" class="url location" href="#">This web page</a> is copyright © 2016 by <span class="fn">Patrick Mooney</span>. <abbr class="summary description" title="Stats explanation for 'Did Donnie Say It?' last updated">Last update to this HTML file</abbr>: <abbr class="dtstart" title="2017-01-27">27 January 2017</abbr>.</p>
</footer>
</div></body>
</html>""")
