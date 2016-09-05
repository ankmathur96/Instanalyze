from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
import requests
import json
import random
import urllib.parse
from instanalyze.logic.secrets import *
import instanalyze.logic.analyze as analyze
N_POSTS_TO_SCRAPE = 100
def random_string(n):
	return ''.join([chr(random.randint(33,126)) for x in range(n)])
# Create your views here.
def index(request):
	return render(request, 'instanalyze/index.html', {})

def authenticate(request):
	redirect_uri = 'http://' + settings.HOST_URL + reverse('instanalyze:authenticate');
	if not request.GET.get('state'):
		return HttpResponseRedirect(reverse('instanalyze:error'))
	if request.GET.get('state') == 'BEGIN':
		scope = 'basic'
		auth_url = 'https://api.instagram.com/oauth/authorize/?'
		sid = 'CODE ' + random_string(16)
		request.session['sid'] = sid
		auth_query = {'response_type' : 'code', 'client_id' : client_id, \
					'scope' : scope, 'redirect_uri' : redirect_uri, 'state' : sid}
		auth_url += urllib.parse.urlencode(auth_query)
		return HttpResponseRedirect(auth_url)
	elif request.GET.get('state').split()[0] == 'CODE':
		code, sid = request.GET.get('code'), request.GET.get('state')
		stored_sid = request.session.get('sid')
		if stored_sid != sid:
			print('State mismatch - security risk - please start again.')
		sid = sid.split()[1]
		request.session['sid'] = sid
		auth_url = 'https://api.instagram.com/oauth/access_token/?'
		auth_query = {'client_id' : client_id, 'client_secret' : client_secret, \
						'grant_type' : 'authorization_code', 'redirect_uri' : redirect_uri, \
						'code' : code, 'state' : sid}
		r = requests.post(auth_url, data=auth_query)
		r = r.json()
		auth_code = r['access_token']
		request.session['auth_code'] = auth_code
		return render(request, 'instanalyze/authorized.html', {'auth_code' : auth_code})
	else:
		return HttpResponseRedirect(reverse('instanalyze:error'))

def process(request):
	auth_code = request.session.get('auth_code')
	auth_url = 'https://api.instagram.com/v1/tags/capitalone/media/recent'
	media_param = {'access_token' : auth_code, 'count' : N_POSTS_TO_SCRAPE}
	r = requests.get(auth_url, params=media_param).json()
	try:
		posts = r['data']
	except Exception:
		print(r)
		raise Exception('Error communicating with Instagram API')
	while len(posts) < N_POSTS_TO_SCRAPE and 'next_url' in r['pagination']:
		r = requests.get(r['pagination']['next_url']).json()
		posts.extend(r['data'])
	print('Got ', len(posts), 'posts')
	print(r['pagination'])
	ordered_top = analyze.top_posts(posts, N_POSTS_TO_SCRAPE)
	for x in ordered_top:
		uid = x['user']['id']
		auth_url = 'https://api.instagram.com/v1/users/' + str(uid) + '/?'
		auth_url += urllib.parse.urlencode({'access_token' : auth_code})
		r = requests.get(auth_url)
		if (int(r.status_code) > 400):
			print('API call failed for ', uid)
			continue
		r = r.json()
		x['user_data'] = r['data']
	ordered_top = analyze.add_sentiment_index(ordered_top)
	request.session['top_posts'] = ordered_top
	return HttpResponseRedirect(reverse('instanalyze:results'))

def results(request):
	top_posts = request.session.get('top_posts')
	binned_results = analyze.bin_by_month(top_posts)
	positive, negative, neutral = 0, 0, 0
	positivity, negativity = 0, 0
	for post in top_posts:
		if 'sentiment' not in post:
			continue
		if post['sentiment'] > 0.08:
			positive += 1
			positivity += post['sentiment']
		elif post['sentiment'] < -0.08:
			negative += 1
			negativity += post['sentiment']
		else:
			neutral += 1
	monthwise_positive, monthwise_negative = [], []
	for k in binned_results:
		pos, neg = 0, 0
		for p in binned_results[k]:
			if 'sentiment' not in p:
				continue
			if p['sentiment'] > 0:
				pos += 1
			else:
				neg += 1
		monthwise_positive.append(pos)
		monthwise_negative.append(neg)
		monthwise_positive.extend([5,6,7])
	for p in top_posts:
		r = requests.get('http://api.instagram.com/oembed', params={'url' : p['link'], 'maxwidth' : 321}).json()
		p['embed'] = r['html']

	return render(request, 'instanalyze/results-2.html', {'top_posts' : top_posts, 'positive' : positive, 'positivity' : round(positivity, 2),\
														'negative' : negative, 'negativity' : round(abs(negativity), 2), 'neutral' : neutral,\
														'monthwise_positive' : monthwise_positive, 'monthwise_negative' : monthwise_negative, \
														'slicedtop' : range(2,len(top_posts))})

def error(request):
	return render(request, 'instanalyze/error.html', {})

