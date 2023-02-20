# Spotify-Bot

A python script for controlling spotify via email, utilizing the imaplib and tekore modules.

The basic idea is to scrape emails from an email account and parse commands from text, which are subsequently 
passed to this script which makes the according API requests via tekore. Emails addresses can be identified as
regular or super users with according command permissions. 

This script requires a registered spotify application and a gmail account with IMAP enabled and an application 
password set. More info on those things bellow.

This script was written for a college dorm situation where people had already been directing the dorm speakers 
over email, but the process had yet to be automated. It's not intended as a rigorous media solution for larger
or smaller applications, but with an intermediate understanding of python it can be scaled accordingly. 

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

Then enable IMAP on the email account. It'll in the settings page under the "Forwarding and POP/IMAP" tab. 

Next, you'll need to go to the management page for the google account the email is under and navigate to the
Security page. There in the "Signing Into Google" block, hit app passwords. It'll ask you sign in again and 
complete some two-step stuff if you have that enabled. Do that, and finally you'll come to a page where you 
can generate the app password. Select "Mail" as the application and "Other (Custom name)" as the device, 
since we won't be using anything on the provided list. Name the password and click "Generate".

This will produce a page with the app password displayed. Copy it, and do not lose it because you're not 
seeing it again. 

Create a file called 'config.yaml' and add the following lines: 

```
user: "gmail-account-here"
password: "app-passowrd-here"
```

where "gmail-account-here" is replaced with the gmail account, and "app-password-here" is replaced with the 
app password.

### Install IMAP and Tekore

If you haven't already, 

`pip install tekore`
and
`pip install imap-tools`

[Tekore docs](https://tekore.readthedocs.io/en/stable/index.html)
[imaplib docs](https://docs.python.org/3/library/imaplib.html)

## Setting Up Users

Make two files call 'users.txt' and 'superusers.txt' respectively. When someone emails the bot, their address
will be checked against the contents these files to see if they have permissions to submit commands. If the 
address is not found within either file, it will be unable to submit any commands. 

When filling out these files with addresses, each line should have only a single address on it. Addresses 
should be spelled correctly and with the proper casing. Addresses should not have a trailing space or any
other extraneous characters like commas at the end of them. 

## Use 

You can start the script by running: 

```
python bump-bot
``` 
In the cloned repository folder. Alternatively, the bump-bot script is an executable with a shebang, so if 
the shebang works with your machine and you add this folder to your $PATH, you'll be able to run bump-bot 
as a command on the terminal anywhere. 

Starting the script prompts you with a simple tui with two options.
```
    [1] : Start The Bot
    [2] : Manual Input
   quit : close the program
```

The first option will activate the bot, meaning that any emails with valid commands within the account will 
be read and parsed along with all incoming emails while the bot is active. To drop out out of this, Ctrl-c 
will bring you back to the tui command line. The second will be explained further in this section. 

This script uses a very simple user/superuser system to determine how people can interact with the bot.
Regular users can queue a track every three minutes, and queue an album or a playlist once per hour. Super 
users can do what regular users can do, but can also use the "priority" version of each command which inserts
whatever track, album,or playlist has been searched into the queue in the next position, and then immediately 
skips to play it while rebuilding the queue that came before it so as not to lose songs that have been queued
in the meantime. Superusers can also pause and play the current playback, as well as adjust the volume.

Now, here's some generic examples of the valid commands that you would send via email: 

```
bump track;

bump:a album; 

bump:p playlist;
```
A line is recognized as a command once the string "bump" is parsed by the script. The script then checks for
a 'suffix' on the bump consisting of a semicolon and a character which determines the type of the thing the
bot is about to search for. Whatever comes after the space separating the bump and the rest of the command is
the string that is fed to the spotify search API, specifically searching for only things that match what ever
the suffix was. The command is then terminated by a semicolon. A command cannot contain line breaks or else 
it will not be recognized (which means it all has to be on the same line in the email).

The top-most line is the standard bump command which queues a single track. This command doesn't have the 
"suffix" that serves as the first string flag mentioned above because it'll probably be the most common. 
'track' in this case replaces the search string, which is what spotify will look for to queue. 

The second line is an example of a command that queues an album. This command carries the suffix "a", and 
'album' in this case replaces the search string, which is what spotify will look for to queue. 

The third line is an example of a command that queues a playlist (searched from the user account). This 
command carries the suffix "p", and 'playlist' in this case replaces the search string, which is what spotify
will look for to queue. 

Now, for the superuser commands: 

```
bump:pt track;
bump:pa album; 
bump:pp playlist;
```
Each of these commands does exactly what their regular counterparts do, but then shuffle they shuffle the 
queue around so whatever they added gets played immediately instead of whatever came before it.

Finally, the superuser commands for playing, pausing, and adjusting the volume of the playback are: 
 
```
bump:play;
bump:pause; 
bump:v volume;
```

The pause and play commands only have a suffix since there's nothing to search for. The volume command uses 
what would have been the search string as the value for volume. This value has to be a number ranging from 0
to 100 in representation of the percentage of the volume that's active.

---Manual Input---

Manual Input is activated with the 2nd option in the tui. It's useful primarily for debugging if you want to 
toy around with the script and interact with the bot locally instead sending an email every time you want to 
test something. Activating it will bring up a repeating two part prompt which will ask for the 'search string' 
(name of the song, album, or playlist to be searched for), and the 'command type', which is what the suffixes 
are from the email commands above. Entering the suffix for the corresponding command type is done without the 
semicolon present in the email commands (for a track, just enter nothing). You can return to the tui command 
line by entering 'quit' as the command type or by hitting Ctrl-c. 

---

If everything in setup went accordingly, the script should be ready to use. Fire up a spotify session and play 
a couple seconds of a song to make sure it's really "active" for the script to use. 

The script can be started by running `python bump-bot`. By default, this will trigger the email listening 
functionality wherein any new emails will be processed for valid commands and fed to the script. If you just 
want to lest it locally, open up main.py and uncomment the line invoking the "local" function. Running it 
again will cause a continuous prompt in the terminal for the search_string and the command type. 

### Credits

This script was largely based on / stitched together from code by magician11 and bnsreenu, who's tutorials on
tekore and email scraping with python were the first ones that I stumbled across in throwing this together.

[Tekore Tutorial](https://www.youtube.com/watch?v=8OGpz0UeYp4)
[Email Tutorial](https://www.youtube.com/watch?v=K21BSZPFIjQ)
