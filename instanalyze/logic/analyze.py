from instanalyze.logic import sentiment as sentiment
import time
import datetime
def output_post(p):
	print('*************************************')
	print('Post by: ', p['user']['username'])
	print('Link: ', p['link'])
	print('Number of likes', p['likes']['count'])
	if 'caption' in p:
		print('Caption:', repr(p['caption']['text']))
	if 'sentiment' in p:
		print('Sentiment:', p['sentiment'])

def top_posts(data, n):
	posts = []
	for p in data[:n]:
		if p is None:
			continue
		dtime = datetime.date.fromtimestamp(float(p['created_time']))
		if dtime.year < 2015:
			continue
		p['year'], p['month'], p['day'] = dtime.year, dtime.month, dtime.day
		posts.append(p)
	ordered_posts = sorted(posts, key=lambda x: x['likes']['count'])[::-1]
	print('I have', len(ordered_posts))
	return ordered_posts

def add_sentiment_index(posts):
	scores = sentiment.load_scores()
	for i, p in enumerate(posts):
		print('analyze', i)
		if p is not None and 'caption' in p and p['caption'] is not None and 'text' in p['caption']:
			p['sentiment'] = sentiment.analyze_sentence(p['caption']['text'], scores)
		# output_post(p)
	return posts

def add_sentiment_index_ml(posts):
	classifier = sentiment.load_classifier()
	scores = sentiment.load_scores()
	for p in posts:
		p['sentiment'] = sentiment.analyze_sentence_ml(p['caption']['text'], classifier, scores)
		output_post(p)
	return posts

def bin_by_month(posts):
	post_binned = {}
	for p in posts:
		if p['month'] not in post_binned:
			post_binned[p['month']] = [p]
		else:
			post_binned[p['month']].append(p)
	return post_binned

