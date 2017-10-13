#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Part of Patrick Mooney's TrumpTweets project. This rotates which known tweets
from both relevant accounts are used in the project's accompanying web quiz.
The accompanying quiz can be seen or taken at https://is.gd/trump_tweets_quiz.

This program is copyright 2017 by Patrick Mooney; it is free software, licensed
under the GPL, either version 3 or (at your option) any later version. See the
file LICENSE.md for details.
"""

import subprocess
import trump_maint as tm

tm.export_plaintext_tweets()
subprocess.call('sync-website.sh', shell=True)