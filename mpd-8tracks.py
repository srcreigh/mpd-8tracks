#####################################
# Project: mpd8tracks
# Author: Shane Creighton-Young
# Copyright: Freely distributable
#
# Usage: 
# python mpd8tracks [url to an 8tracks mix]
#
# Dependencies:
# - bash shell
# - mpd and mpc
# - an 8tracks developer api key
#
# Recommended:
# - another mpd client to actually manage the music playing
#
# Notes:
# - another song will be added if the playlist is changed at all
# - doesn't queue another playlist automatically; only exits
#
# Known issues:
#
#

import sys
import urllib2
import os
import json

# Open the API developer key
api_key = raw_input("Enter API Key: ")

# we're using api version 2
api_version = "2"

def api_call(path, **kwargs):
   query = "https://8tracks.com/%s.jsonp?api_version=%s&api_key=%s" % (path, api_version, api_key)
   for key in kwargs:
      query = "%s&%s=%s" % (query, key, kwargs[key])
   return json.loads(urllib2.urlopen(query).read())


# Check for correct usage (i.e. that a url has been given)
if (len(sys.argv) != 2):
   print >> sys.stderr, "ERR: Usage: python mpd8tracks [url to an 8tracks mix]"
   sys.exit(2)
else:
   mix_url = sys.argv[1]



# Check that MPD/MPC is working
if (os.system('mpc 1>/dev/null 2>/dev/null') != 0):
   print >> sys.stderr, "ERR: MPD isn't running; please start mpd and run again"
   sys.exit(1)

# Set up mpd
os.system("mpc clear 1>/dev/null")
os.system("mpc consume on 1>/dev/null")

# Get the mix information, extract the mix id
mix_info = api_call(mix_url[19:])
mix_id = mix_info['mix']['id']
mix_name = mix_info['mix']['name'].encode('ascii', 'ignore')

os.system("mkdir \"playlists/%s\" 1>/dev/null 2>/dev/null" % mix_name)

# Get the play token
play_token_info = api_call("sets/new")
play_token = play_token_info['play_token']

# Start the playlist
song_info = api_call("sets/1/play", mix_id=mix_id, play_token=play_token)

# Song playing loop
while True:

   # Get relevant information and save it
   if song_info['set']['at_end']:
      break

   track_id = song_info['set']['track']['id']
   name = song_info['set']['track']['name'].encode('ascii', 'ignore')
   artist = song_info['set']['track']['name'].encode('ascii', 'ignore')
   track_url = song_info['set']['track']['url']

   print "Playing: %s - \"%s\"" % (artist, name)

   # Notify 8tracks that the song is being played
   api_call("sets/1/report", play_token=play_token, mix_id=mix_id, track_id=track_id)

   # Queue the song via mpc
   os.system("mpc add \"%s\" 1>/dev/null" % track_url)
   os.system("mpc play 1>/dev/null")
   f = urllib2.urlopen(track_url)
   with open("playlists/%s/%s - %s.m4a" % (mix_name, artist, name), "w+") as code:
      code.write(f.read())
   
   # Wait until the song finishes playing to do the loop again
   # (note: in reality, this just waits for *something* to happen to the
   #  playlist. this could be neater)
   os.system("mpc current --wait 1>/dev/null")

   # Load the next song
   song_info = api_call("sets/1/next", play_token=play_token, mix_id=mix_id)

