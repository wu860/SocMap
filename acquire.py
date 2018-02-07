#!/usr/bin/env python3

# Dependencies
import tweepy, os, jsonpickle

class Tweet(object):
	def __init__(self, user, text, timestamp, mentions):
		self.user = user
		self.text = text
		self.timestamp = timestamp
		self.mentions = mentions

class Retweet(Tweet):
	def __init__(self, user, text, timestamp, mentions, source, retweets):
		super().__init__(user, text, timestamp, mentions)
		self.source = source
		self.retweets = retweets

# When you hit the Twitter API for too long it blocks for 15 minutes
# we'll just wait around for that.
def limit_handled(cursor):
	while True:
		try:
			yield cursor.next()
		except tweepy.RateLimitError:
			time.sleep(15 * 60)

# Returns whether we have tweets from a particular user stored
def userTweetsPresent(username, tweetdir):
	return os.path.isfile(tweetdir + "/" + username + ".json")

# Returns the usernames of people mentioned in a body of text
def getMentionsFromText(text):
	return []

# Downloads, parses, and saves tweets for a user
def getUserTweets(api, username, tweetdir, numtweets):
	cursor = tweepy.Cursor(api.user_timeline, user_id=username, count=numtweets)
	tweets = []
	for tweet in limit_handled(cursor.items()):
		mentions = getMentionsFromText(tweet.text)
		date = tweet.created_at
		text = tweet.text
		source = tweet.user.screen_name
		if( hasattr(tweet, "retweeted_status") ):
			orig_author = tweet.retweeted_status.user.screen_name
			rt_count = tweet.retweeted_status.retweet_count
			rt = Retweet(source, text, date, mentions, orig_author, rt_count)
			tweets.append(rt)
		else:
			tw = Tweet(source, text, date, mentions)
			tweets.append(tw)
	tweetDump = jsonpickle.encode(tweets)
	f = open(tweetdir + "/" + username + ".json", "w")
	f.write(tweetDump)
	f.close()

# Parse user tweets, return [[people they mentioned], [people they retweeted]]
def getUserReferences(username, tweetdir, workdir):
	tweetfile = open(tweetdir + "/" + username + ".json", "r")
	blob = tweetfile.read()
	tweets = jsonpickle.decode(blob)
	tweetfile.close()
	retweeted = set()
	mentioned = set()
	for tweet in tweets:
		if( isinstance(tweet, Retweet) ):
			retweeted.add(tweet.source)
		else:
			for user in tweet.mentions:
				mentioned.add(user)
	return [mentioned, retweeted]

def deleteUserTweets(username, tweetdir):
	os.unlink(tweetdir + "/" + username + ".json")

def getLayers(api, numLayers, options, userlist):
	nextLayerRTs = dict()
	nextLayerMentions = dict()
	for username in userlist:
		if( not userTweetsPresent(username, options.tweetdir) ):
			getUserTweets(api, username, options.tweetdir, options.numtweets)
			mentions, rts = getUserReferences(username, options.tweetdir, options.workdir)
			if( len(rts) > 0 ):
				nextLayerRTs[username] = list(rts)
			if( len(mentions) > 0 ):
				nextLayerMentions[username] = list(mentions)
	print("Next layer retweets: ", nextLayerRTs)
	print("Next layer mentions: ", nextLayerMentions)