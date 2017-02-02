### Accessing Custom Post Types

If you have Jetpack installed on your Wordpress site, you can activated the REST API. This opens up a whole new world for WordPress. It gives you the ability to make WordPress headless. Meaning, you can completely separate your back-end and your front-end and use one of those Javascript frameworks all the cool kids are using to build out your entire front end.

When you activate this plugin, your REST API is instantly activated. However, this only gives you the ability to access your Post and your Page post types. If you have custom post types you need do a little more work. In your `functions.php` file, add the following:

~~~~
/** replace 'recipe' with your custom post type **/
function rest_custom_post( $allowed_post_types ) {
$allowed_post_types[] = 'recipe';
return $allowed_post_types;
}
add_filter( 'rest_api_allowed_post_types', 'rest_custom_post' );
~~~~

I am using the `rest_api-allowed_post_types` filter to allow my custom post type `recipe` to be used in the REST API. You can test this by logging into [WordPress.com][3] or by trying out Automattic's new tool, and potential replacement for wp-admin, [Calypso][4]. Both of these tools utilize the API so if you see your custom post type displayed, then it is working.

Now that we can use the API properly, lets start building out our Python bot. I will be building this in Python 3.4. Here is essentially what I want this bot to accomplish:

1. Connect to the API endpoint filtering out posts from only the recipe post type.
2. Find the total amount of posts returned.
3. Generated a random number between 1 and the total returned posts (step 2).
4. Find the post title and url.
5. Find a media attachment url within the post that ends with '-main.jpg'.
6. Save and open image locally from the media attachment url (step 5).
7. Post to twitter using Twython

First, we need to import what we are going to use for this script.

~~~~
from twython import Twython, TwythonError
import json
from random import randint
import urllib.request
import ssl #may or may not need this
import requests
~~~~

As mentioned, we will be using the [Twython][5] wrapper to handle posting to twitter. We will also be parsing JSON so we will need `json` and `urllib` libraries as well as `randint` for creating a random number. You may or may not need to import `ssl` as it seemed to be necessary for running this on macOS Sierra, but not on Raspbian.

Next is to access your rest API using the `/posts/' endpoint found on the [WordPress developer][6] site. It will look like this:

~~~~
https://public-api.wordpress.com/rest/v1.1/sites/bakingbrew.com/posts
~~~~

All you have to do is replace `bakingbrew.com` with your site. Now this will return all your posts, but we don't want this. We want to just return posts from the `recipe` post type. There are plenty of query parameters that will help you filter out your WordPress content to your liking. For my purposes, I queried `type=recipe` to query my custom post type, `number=100` to return only 100 posts, and `order=DESC` to filter content in descending order. Now my endpoint looks something like this:

~~~~
https://public-api.wordpress.com/rest/v1.1/sites/bakingbrew.com/posts/?pretty=true&type=recipe
~~~~

If you use `curl` or simply type this in the web browser, it will spit out JSON of your content. Great. Now lets parse it!

~~~~
#In this example, we are querying post type recipe, 100 posts, and ordering in descending order
url = 'https://public-api.wordpress.com/rest/v1/sites/bakingbrew.com/posts/?type=recipe&number=100&order=DESC';

#make the request
response = urllib.request.urlopen(url)

#decode json
data = json.loads(response.read().decode('utf-8'))

~~~~

Use `urllib.request` to open the url and decode the response. If you `print(data)`, you will see the JSON:

~~~~

{
"found": 63,
"posts": [
{
"ID": 2745,
"site_ID": 74619306,
"author": {
"ID": 1,
"login": "kylevalenzuela",
"email": false,
"name": "Kyle",
"first_name": "Kyle",
"last_name": "Valenzuela",
"nice_name": "kylevalenzuela",
"URL": "http://bakingbrew.com",
"avatar_URL": "",
"profile_URL": "https://en.gravatar.com/3931070877ecadc7477efde65a4b9891"

...

~~~~

See the `found` object? It returns the number of posts found during the request. We will use this as our max value when creating a random number.

~~~~
found_posts = data['found']
rand_num = randint(0, FOUND_POSTS)
print("Your random number is: %s", %s rand_num)
~~~~

Here we use `randint` to generate a random number between 1 and the number of returned posts.

~~~~
title = data['posts'][RAND_NUM]['title'] 
print("The chosen bread!!!!: " + title)
recipe_url = data['posts'][RAND_NUM]['URL']
~~~~

Our random number will be used to find the nth item in the list. Confining the max number to the number of returned posts will generate a number within the bounds of our response. Use this number to find the post's title and url.

~~~~

#returns recipe post image url
#looks through media and finds the image containing "...main.jpg"
x = data['posts'][rand_num]['attachments']
for n in x.values():
if 'main.jpg' in n['URL']:
media_url = n['URL']
~~~~

Next we want to find the image post url. However, I am looking for a particular media attachment from a recipe post. This image contains contains the string 'main.jpg' so I want to look at each media attachment in a post and check to see if it contains the string 'media.jpg'. This is not a good approach however. A better approach would be to access the media via custom post meta (from ACF fields). I plan on doing a follow up using this approach. For now, we iterate through media attachments.

~~~~
#saves recipe post image url to local folder as temp.jpg
urllib.request.urlretrieve(media_url, "temp.jpg")

#opens the image
photo = open('temp.jpg', 'rb')
~~~~

Now that our `media_url` is stored in a variable, we need to download it locally. Twython requires you to upload an image from your local machine. You can't use a url to upload media to twitter. `urlretrieve' will download an image from a url. Pass `media_url` and save the file as `temp.jpg` in the current working directory. After you save the image, use `open` to open it. `rb` gives use both read a write access to the file.

~~~~
app_key = ''
app_secret = ''
oauth_token = ''
oauth_token_secret = ''

#Twitter authentication
twitter_auth = Twython(app_key, app_secret, oauth_token, oauth_token_secret)
~~~~

Now that we acquired everything needed for the tweet, we need to use Twython to authenticate. Head on over to the [Twitter Developer Portal][7] and create an app. Navigate to the Key and Access Tokens tab and grab the app key and secret and your oauth token and secret.

~~~~
#creates the tweet
the_tweet = title + ' ' + recipe_url

#upload image to twitter
media_now = twitter_auth.upload_media(media=photo)

print("Posting your terrible photos to twitter!")

#posts to twitter
#status is post title, media is the uploaded post image
twitter_auth.update_status(status=the_tweet, media_ids=[media_now['media_id']])

#print success
print("Open a beer! Your work is done")
~~~~

First, we build out the text portion of the tweet by concatenating the title and the recipe url. Then we upload our image and post the tweet! Use `print` when tweet completes.

Finally, run your script in the terminal:

~~~~
python3 bb_twitter_bot.py
~~~~

You should see the following output:

~~~~
Kyles-MacBook-Pro:bakingbrew_twitter_bot Kyle$ python3 bb_twitter_bot.py
Your random number is:
48
The chosen bread!!!!: Double Stout Chocolate Chip Cookies
Posting your terrible photos to twitter!
Open a beer! Your work is done
Kyles-MacBook-Pro:bakingbrew_twitter_bot Kyle$
~~~~

And if you navigate to Twitter, you should see your tweet posted.

<blockquote class="twitter-tweet" data-lang="en"><p lang="en" dir="ltr">Cosmic Ristretto Chocolate Bites <a href="https://t.co/sRiD0VZXfq">https://t.co/sRiD0VZXfq</a> <a href="https://t.co/9r952x05WB">pic.twitter.com/9r952x05WB</a></p>&mdash; Baking Brew (@bakingbrew) <a href="https://twitter.com/bakingbrew/status/826854469644062720">February 1, 2017</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

### SSL Issues

On macOS Sierra, I experienced an the following issue:

~~~~
"urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:749)>"
~~~~

I attempted the following:

~~~~
import ssl
context = ssl._create_unverified_context()

#make the request
response = urllib.request.urlopen(url, context)
~~~~

But received the same issue. I found the following solution on Stack Exchange[8]:

~~~~
##ssl._create_default_https_context = ssl._create_unverified_context #needed for MacOS Sierra.

ssl._create_default_https_context = ssl._create_unverified_context
~~~~

However, this approach is highly discouraged and is seen as a quick fix This issue only occurrs on macOS Sierra. I did not experience this issue running it on my raspberry pi.

### Automating

Now that are script is up and running, the next step is to automate it. Lets make a cronjob to make this happen.

~~~~
crontab -e
~~~~

And add the following:

~~~~
23 * * * * python3 /url/to/your/script.py
~~~~

Here is the script in its entirety: 

~~~~
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
~~~~

This will run the script on the 23rd minute of every hour (1:23pm for example). I don't like posting at the top of the hour so I made it a random minute. 

And that is it. If you find any interesting and creative uses for using the Wordpress REST API, be sure to share. This was my first time using Python 3 so I'm sure some refactoring is in order. For one, I need access to my Advanced Custom Fields in my REST API. Looping through my media attachments for a particular string is just waiting for a disaster to happen. 

[1]: https://bakingbrew.com
[2]: http://bufferapp.com/
[3]: http://wordpress.com
[4]: https://developer.wordpress.com/calypso/
[5]: https://github.com/ryanmcgrath/twython
[6]: https://developer.wordpress.com/docs/api/1.1/get/sites/%24site/posts/
[7]: https://dev.twitter.com/
[8]: http://stackoverflow.com/questions/27835619/ssl-certificate-verify-failed-error