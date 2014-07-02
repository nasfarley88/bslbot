#!/usr/bin/env python



# I used these to generate my first config file. Might be useful in the future

def urlify(s):
    s = re.sub(r"[^\w\s]", '', s)
    s = re.sub(r"\s+", '-', s)
    return s

#for i in all_my_videos:
#    tmpkey = urlify(i['name']).lower()
#    tmptweet = 'How to sign ' + re.sub(r" \(.*\)", r"", i['name']) + ' in #BSL'


## real code starts here

import tweepy
import time
import sys
import os
import random
from configobj import ConfigObj

config = ConfigObj(os.path.expanduser('~/.bslbot'), unrepr=True)

auth = tweepy.OAuthHandler(config['authentication']['consumer_key'], config['authentication']['consumer_secret'])
auth.set_access_token(config['authentication']['access_key'], config['authentication']['access_secret'])
api = tweepy.API(auth)

def printOrTweet(x):
    """Simple function that currently prints, but will tweet."""
    # print x
    print "You have entered the printOrTweet zone."
    api.update_status(x)

def tweetRandomWord():
    # TODO sort it so that 'Random' actually means 'random selection from tweets that haven't been tweeted yet'
    import random
    """This function tweets a pseudo random word in BSL."""
    # Dictionary of all words we can possibly tweet about
    all_words = config['Tweets']['Words'] 

    # Choose one of the words
    word = all_words[random.choice(all_words.keys())]
    tweet = word['tweet']
    link = word['link']
    printOrTweet(tweet + "\n" + link)


def tweetAbout(category):
    """Function to choose a semi-random tweet from a predefined list.

    This function looks at all the tweets in a category and then chooses one
    that has not been used in a while. Specifically, it chooses tweets which
    have been tweeted the least.

    E.g. If all but 10 tweets in a category have been tweeted once, and 10 have
    never been tweeted, this function will only choose from those 10."""

    chosen_tweet = random.choice(config['tweets'][category].keys())
    tmptweet = config['tweets'][category][chosen_tweet]['tweet']
    try:
        tmptweet = tmptweet + "\n" + config['tweets'][category][chosen_tweet]['link']
    except NameError:
        print "No link for this one!"
    
    config['tweets'][category][chosen_tweet]['no_of_times_tweeted'] +=1
    config.write()
    
    return tmptweet
    

def _whatShouldITweetAbout():

    """Internal function allowing bslbot to decide what to tweet about.

    Returns string."""

    free_will =  random.random()
    
    if free_will <0.005:
        return tweetAbout('selfpromotion')
    elif free_will <0.2:
        return tweetAbout('advice')
    else:
        return tweetAbout('words')
    

def tweet(text=None, delay=0):
    """Function instructing bslbot to tweet.

    If no arguments are given, bslbot decides what to tweet on his own."""

    import time
    time.sleep(delay)
    
    if text==None:
        printOrTweet(_whatShouldITweetAbout())
    else:
        printOrTweet(text)


if __name__ == "__main__":
    print "Starting bslbot..."
    tweet(delay=random.randint(1,3400))
