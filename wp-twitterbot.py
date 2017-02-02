from twython import Twython, TwythonError
import json
from random import randint
import urllib.request
import ssl #may or may not need this
import requests

ssl._create_default_https_context = ssl._create_unverified_context #needed for MacOS Sierra. Not required on Pixel / Raspberry Pi

#Put your Twitter credentials here! 
#https://apps.twitter.com/

app_key = ''
app_secret = ''
oauth_token = ''
oauth_token_secret = ''



#Your Wordpress Jetpack REST API Endpoint for querying posts
#https://developer.wordpress.com/docs/api/1.1/get/sites/%24site/posts/
#In this example, we are querying post type recipe, 100 posts, and ordering in descending order 
url = 'https://public-api.wordpress.com/rest/v1/sites/bakingbrew.com/posts/?type=recipe&number=100&order=DESC';

#make the request
response = urllib.request.urlopen(url)

#decode json
data = json.loads(response.read().decode('utf-8'))

#returns number of posts returned from response [<--rolls off the tongue weird]
found_posts = data['found']

#returns a random number from 1 to number of returned posts
rand_num = randint(0, found_posts)

#prints random number
print("Your random number is: ")
print(rand_num)

#return recipe post title
title = data['posts'][rand_num]['title'] 

#prints recipe post title
print("The chosen bread!!!!: " + title)

#returns recipe post url
recipe_url = data['posts'][rand_num]['URL']

#creates the tweet
the_tweet = title + ' ' + recipe_url

#returns recipe post image url
#looks through media and finds the image containing "...main.jpg"
x = data['posts'][rand_num]['attachments']
for n in x.values():
    if 'main.jpg' in n['URL']:
        media_url = n['URL']
   
#saves recipe post image url to local folder as temp.jpg
urllib.request.urlretrieve(media_url, "temp.jpg")

#opens the image
photo = open('temp.jpg', 'rb')

#Twitter authentication
twitter_auth = Twython(app_key, app_secret, oauth_token, oauth_token_secret)

#upload image to twitter
media_now = twitter_auth.upload_media(media=photo)
print("Posting your terrible recipe to twitter!")

#posts to twitter
#status is post title, media is the uploaded post image
twitter_auth.update_status(status=the_tweet, media_ids=[media_now['media_id']])

#print success
print("Open a beer! Your work is done")
