#!/usr/bin/env python

import tweepy
import time
import sys
import os
import random
import gspread
import logging
from configobj import ConfigObj
from subprocess import call





def find_col_or_none(name, wks):
    """A short function which returns None or the column cell. """
    logger = logging.getLogger(__name__)

    try:
        x =  wks.find(name).col
        logger.debug('Column named "' + name + "' is number " + str(x) + ".")
        return x
    except gspread.exceptions.CellNotFound:
        logger.debug('Column named "' + name + "' not found.")
        return None
    
class TwitterBot:
    """A class to make a twitter bot."""

    def __init__(self,
                 config_file=os.path.expanduser('~/.bslbot'),
                 config_ss_name="bslbot's brain",
                 logging_level=logging.DEBUG,
                 remote_media_dir="nasfarley88@nathanda.co.uk:Dropbox/vimeo_drop/gifs/",
                 local_media_dir="~/tmp/",
                 weighted_categories=None):
        "Initiate twitter bot with appropriate config and logins."
        
        logging.basicConfig(level=logging_level)
        self.logger = logging.getLogger(__name__)

        self.logger.debug('Fetching config file')
        self.config = ConfigObj(config_file, unrepr=True)
        self.logger.debug("Current config:\n" + str(self.config))

        self.gc = gspread.login(self.config['gspread']['username'],
                                self.config['gspread']['password'])
        self.config_ss = self.gc.open(config_ss_name)
        
        self._tweepy_auth = tweepy.OAuthHandler(
            self.config['authentication']['consumer_key'],
            self.config['authentication']['consumer_secret'])
        self._tweepy_auth.set_access_token(
            self.config['authentication']['access_key'],
            self.config['authentication']['access_secret'])
        self._tweepy_api = tweepy.API(self._tweepy_auth)

        self.remote_media_dir = remote_media_dir
        self.local_media_dir = local_media_dir

        # TODO: Add some check that the twitter api has connected correctly.

        self.weighted_categories = [('SelfPromotion', 1.0/100),
                                    ('Advice', 10.0/100),
                                    ('BSLDictionary', 89.0/100)]

    def _print_tweet(self, tweet, media=None):
        """Prints the tweet to stdout. """
        self.logger.info('Tweet: ' + str(tweet))
        self.logger.info('Media: ' + str(media))

    def _tweet_tweet(self, tweet, media=None):
        """Tweets the tweet."""

        if media == None:
            self.logger.info('Tweeting...')
            self._tweepy_api.update_status(status=tweet)
        else:
            try:
                self.logger.info('Attempting to scp ' + media)
                scp_return = call('scp',
                                  self.remote_media_dir+media,
                                  self.local_media_dir,
                                  shell=True)

                assert scp_return == 0, "scp returned non-zero value: " + scp_return
                assert os.path.isfile(os.path.expanduser(self.local_media_dir+media)),\
                    self.local_media_dir+media + " does not exist."

                self._tweepy_api.update_with_media(
                    filename=self.local_media_dir+media,
                    status=tweet)

                self.logger.info('Attempting to rm ' + media)
                rm_return = call('rm '+local_media, shell=True)
                self.logger.info('rm return status: ' + rm_return)
                
            except AssertionError as e:
                self.logger.warning('Caught an assertion error: ' + e)
                self.logger.info('Tweeting without media')
                self._tweepy_api.update_status(status=tweet)
                
    def print_or_tweet(self, tweet, media=None):
        """Simple function that prints or tweets based on the config file. """

        if self.config['misc']['printortweet'] == 'print':
            self._print_tweet(tweet, media)
        elif self.config['misc']['printortweet'] == 'tweet':
            self._tweet_tweet(tweet, media)

    def _choose_category(self):
        """Shamelessly stolen from
        http://stackoverflow.com/questions/3679694/a-weighted-version-of-random-choice.

        """
        total = sum(w for c, w in self.weighted_categories)
        r = random.uniform(0, total)
        upto = 0
        for c, w in self.weighted_categories:
            if upto + w > r:
                return c
            upto += w
        assert False, "Shouldn't get here"

        
    def choose_tweet_from_category(self, category):
        """Fetch tweet and media from spreadsheet. """

        # Refresh the connection to google sheets
        self.gc.login()
        
        wks = self.config_ss.worksheet(category)

        # TODO: I don't like this, fetching all the values is inefficient. 
        wks_list = wks.get_all_values()

        tweet_cell_col = wks.find("Tweet").col
        no_of_times_tweeted_cell_col = wks.find("No of times tweeted").col

        link_cell_col = find_col_or_none("Link", wks)
        media_cell_col = find_col_or_none("Media", wks)

        # Remove the titles
        wks_list.pop(0)

        lowest_no_of_times_tweeted = 9001
        candidates_for_tweeting = []
        for i in wks_list:
            # -1 in the next line because python counts from 0, spreadsheets count
            # from 1
            no_of_times_tweeted = int(i[no_of_times_tweeted_cell_col-1])
            if no_of_times_tweeted < lowest_no_of_times_tweeted:
                # if this tweet has the lowest no_of_times_tweeted so far dump the
                # rest of them and start the list with this one
                lowest_no_of_times_tweeted = no_of_times_tweeted
                logging.debug("lowest_no_of_times_tweeted reduced to "+str(no_of_times_tweeted))

                # Start the list again with the current tweet
                candidates_for_tweeting = [ i ]
            elif no_of_times_tweeted == lowest_no_of_times_tweeted:
                # otherwise if it's equally untweeted, carry on and add this one to
                # the list
                candidates_for_tweeting.append(i)

        chosen_tweet = random.choice(candidates_for_tweeting)

        cell_for_chosen_tweet = wks.find(chosen_tweet[tweet_cell_col-1])

        tweet_to_return = wks.cell(cell_for_chosen_tweet.row, tweet_cell_col).value + \
                          " " + self.config['misc']['signature']

        if link_cell_col is not None:
            tweet_to_return += "\n" + wks.cell(cell_for_chosen_tweet.row, link_cell_col).value

        self.logger.debug("Cell: " + str(wks.cell(cell_for_chosen_tweet.row, 5)))
        self.logger.debug("Cell value: " + str(wks.cell(cell_for_chosen_tweet.row, 5).value))

        current_no_of_times_tweeeted = int( wks.cell( cell_for_chosen_tweet.row,
                                                      no_of_times_tweeted_cell_col ).value )

        # Update the number of times tweeted
        wks.update_cell( cell_for_chosen_tweet.row,
                         no_of_times_tweeted_cell_col,
                         current_no_of_times_tweeeted + 1)

        if media_cell_col == None:
            return (tweet_to_return, None)
        else:
            return (tweet_to_return, 
                    wks.cell(cell_for_chosen_tweet.row, media_cell_col).value)

    def tweet_for_self(self, delay=None):
        if delay is None:
            delay = random.randint(1, self.config['misc']['max_delay'])

        time.sleep(delay)
        
        chosen_tweet, chosen_media = self.choose_tweet_from_category(self._choose_category())
        self.print_or_tweet(chosen_tweet, media=chosen_media)

    def auto_follow_back(self):
        """Follow back people automatically. """

        for follower in tweepy.Cursor(self._tweepy_api.followers).items():
            if follower._json['protected'] is False:
                follower.follow()
        


if __name__ == '__main__':
    bot = TwitterBot()
    # bot.auto_follow_back()
    bot.tweet_for_self()
