# Spotify-Bot

A python script for controlling spotify via email, utilizing the imaplib and tekore modules.

The basic idea is to scrape emails from an email account and parse commands from text, which are subsequently 
passed to this script which makes the according API requests via tekore. Emails are filtered from a whitelist, 
and can be identified as regular or super users with according command permissions. 

This script requires a registered spotify application and a gmail account with IMAP enabled and an application 
password set. More info on those things bellow.

This script was written for a college dorm situation where people had already been directing the dorm speakers 
over an email chain, but the process had yet to be automated. It's not intended as a rigorous media solution for 
larger or smaller applications, but with an intermediate understanding of python it can be scaled accordingly. 

## Setup

### Clone this repository

`git clone https://github.com/Chichri/Spotify-Bot.git`

### Spotify Account Application

Spotify allows you to autonomously control the activity on an account with an "application". You'll need to 
login to your spotify account and make one, which you can do [here](https://developer.spotify.com/dashboard/applications).

Once you do so, create a file called 'creds.config' and add the following lines: 

```
[DEFAULT]
SPOTIFY_CLIENT_ID = xxx
SPOTIFY_CLIENT_SECRET = yyy
SPOTIFY_REDIRECT_URI = https://example.com/callback
```

where xxx and yyy are replaced with the client id and client secret of the spotify application.

### Add a refresh token to your config file

Then add a refresh token to the config file by running

`python get_refresh_token.py`

This will prompt a page in your browser asking for all permission for the bot. Hit accept and save the url it
redirects to. Go back to the terminal you ran this in and give the url. 

You'll then see in your `creds.config` the added line

`SPOTIFY_USER_REFRESH = refresh-token-here`

### Email Account Configuration

I would recommend making a new gmail account for your bot to avoid spamming any accounts you actually use.

Once you do that, enable IMAP on the email account. It'll in the settings page under the "Forwarding and POP/IMAP" tab. 

Next, you'll need to the management page for the google account the email is under and navigating to the Security page.
There in the "Signing Into Google" block, hit app passwords. It'll ask you sign in again / complete some two-step stuff 
if you have that enabled. Do that, and finally you'll come to a page where you can generate the app password. Select 
"Mail" as the application and "Other (Custom name)" as the device, since we won't be using anything on the provided 
list. Name the password and click "Generate".

This will produce a page with the app password displayed. Copy it, and do not lose it because you're not seeing it again. 

Create a file called 'config.yaml' and add the following lines: 

```
user: "gmail-account-here"
password: "app-passowrd-here"
```

where "gmail-account-here" is replaced with the gmail account, and "app-password-here" is replaced with the app password.

### Install IMAP4 and Tekore

If you haven't already, 

`pip install tekore`
and
`pip install imap4`

[Tekore docs](https://tekore.readthedocs.io/en/stable/index.html)
[imaplib docs](https://docs.python.org/3/library/imaplib.html)

## Use 

The core functionality of script is scraping two strings out of the email. The first is fed to the search functionality of the
spotify API, and returns the song/album id of whats being searched for the script to play. The second acts as a flag for script
to either search specifically for a track, or an album.

Regular users can queue a track every three minutes, and queue an album once per day. Super users can do what regular users can 
do, but can also use the "priority" command which inserts whatever track has been searched into the queue in the next position, 
and then immediately skips to play it. 

If everything in setup went accordingly, the script should be ready to use. Fire up a spotify session and play a couple seconds
of a song to make sure it's really "active" for the script to use. 

The script can be started by running `python main.py`. By default, this will trigger the email listening functionality wherein 
any new emails will be processed for valid commands and fed to the script. If you just want to lest it locally, open up main.py 
and uncomment the line invoking the "local" function. Running it again will cause a continuous prompt in the terminal for the
search_string and the command type. 

### Credits

This script was largely based on / stitched together from code by magician11 and bnsreenu, who's tutorials on tekore 
and email scraping with python were the first ones that I stumbled across in throwing this together.

[Tekore Tutorial](https://www.youtube.com/watch?v=8OGpz0UeYp4)
[Email Tutorial](https://www.youtube.com/watch?v=K21BSZPFIjQ)
