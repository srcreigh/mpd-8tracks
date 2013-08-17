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
api_key = open("8tracksdevkey.txt", 'r').readline()[:-1]

# Check for correct usage (i.e. that a url has been given)
if (len(sys.argv) != 2):
   print "ERR: Usage: python mpd8tracks [url to an 8tracks mix]"
   sys.exit(2)
else:
   mix_url = sys.argv[1]

# we're using api version 2
api_version = "2"

# Check that MPD/MPC is working
if (os.system('mpc 1>/dev/null 2>/dev/null') != 0):
   print "ERR: MPD isn't running; please start mpd and run again"
   sys.exit(1)

# Set up mpd
os.system("mpc clear 1>/dev/null")
os.system("mpc consume on 1>/dev/null")

# Get the mix information, extract the mix id
query_url = "%s.jsonp?api_version=%s&api_key=%s" % (mix_url, api_version, api_key)
mix_info = json.loads(urllib2.urlopen(query_url).read())

mix_id = mix_info['mix']['id']
mix_name = mix_info['mix']['name'].encode('ascii', 'ignore')

os.system("mkdir \"playlists/%s\" 1>/dev/null 2>/dev/null" % mix_name)

# Get the play token
query_url = "http://8tracks.com/sets/new.jsonp?api_version=%s&api_key=%s" % (api_version, api_key)
play_token_info = json.loads(urllib2.urlopen(query_url).read())
play_token = play_token_info['play_token']

# Start the playlist
query_url = "http://8tracks.com/sets/460486803/play.jsonp?api_version=%smix_id=%s" % (api_version, mix_id)
query_url += "&api_key=" + api_key
query_url += "&play_token=" + play_token

song_info = json.loads(urllib2.urlopen(query_url).read())

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
   query_url = "http://8tracks.com/sets/%s/report.xml" % play_token
   query_url += "?mix_id=%s" % mix_id
   query_url += "&track_id=%s" % track_id
   query_url += "&api_key=" + api_key
   # note: do not need to save any information, just need to call the url
   urllib2.urlopen(query_url) 

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
   query_url = "http://8tracks.com/sets/%s/next.jsonp" % play_token
   query_url += "?mix_id=%s" % mix_id
   query_url += "&api_key=" + api_key
   song_info = json.loads(urllib2.urlopen(query_url).read())
