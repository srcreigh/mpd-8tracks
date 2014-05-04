###################################
# Project: mpd8tracks
# Author: Shane Creighton-Young
#
# Usage: 
# python mpd8tracks [url to an 8tracks mix]...
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
# Contributors:
# omsmith
# xLegoz

import sys
import urllib2
import os
import json
import time

def normalize(s):
   t = s.encode('ascii', 'ignore')
   return t.translate(None, "'/")

def fix_track_url(url):
   if (url[:5] == 'https'):
      return 'http' + url[5:]
   return url

# Open config file
config = None
try:
    with open('config.json') as config_text:
        config = json.load(config_text)
except IOError:
    print >> sys.stderr, "WARN: No config.json file"

# Check that MPD/MPC is working
if (os.system('mpc 1>/dev/null 2>/dev/null') != 0):
   print >> sys.stderr, "ERR: MPD isn't running; please start mpd and run again"
   sys.exit(1)

# Check and process input options, url(s)
mix_urls = []
if (len(sys.argv) == 1):
   print >> sys.stderr, "ERR: Usage: python mpd8tracks [url to an 8tracks mix]..."
   sys.exit(2)
for url in sys.argv[1:]:
   i = url.find("8tracks.com")
   if i != -1:
      mix_urls.append(url[i+11:])

# Open the API developer key
# TODO: Should check that this API key is valid
api_key = None
if (config == None or config['apikey'] == None):
   try:
      api_key = raw_input("Enter API Key: ")
   except KeyboardInterrupt:
      print
      sys.exit(1)
else:
   print "Using API Key from config.json..."
   api_key = config['apikey']

# we're using api version 3
api_version = "3"

def api_call(path, **kwargs):
   query = "https://8tracks.com/%s.jsonp?api_version=%s&api_key=%s" % (path, api_version, api_key)
   for key in kwargs:
      query = "%s&%s=%s" % (query, key, kwargs[key])
   return json.loads(urllib2.urlopen(query).read())

# Set up mpd
os.system("mpc clear 1>/dev/null")
os.system("mpc consume on 1>/dev/null")

# Get the play token
play_token_info = api_call("sets/new")
play_token = play_token_info['play_token']

for mix_url in mix_urls:
   # Get the mix information, extract the mix id
   mix_info = api_call(mix_url)
   mix_id = mix_info['mix']['id']
   mix_name = normalize(mix_info['mix']['name'])
   download = config.get('download', False)

   # Create the playlist directory if we're downloading the music
   if (download):
       os.system("mkdir -p \"playlists/%s\" 1>/dev/null 2>/dev/null" % mix_name)

   # Let the user know which mix is playing
   print "Now playing: \"%s\"" % mix_name

   # Song playing loop
   while True:

      # Get the song info crom 8tracks api
      song_info = api_call("sets/%s/next" % play_token, mix_id=mix_id)

      # If we can't request the next one due to time restrictions, sleep and try again
      if (song_info['status'] == "403 Forbidden"):
        time.sleep(30)
        continue
      
      # Get relevant information and save it
      track_id = song_info['set']['track']['id']
      artist = normalize(song_info['set']['track']['performer'])
      name = normalize(song_info['set']['track']['name'])
      track_url = song_info['set']['track']['track_file_stream_url']

      # Fix the track URL (https://api.soundcloud/foo links don't work and need
      # to be converted to http://api.soundcloud/foo)
      track_url = fix_track_url(track_url)

      print "Enqueuing: %s - \"%s\"" % (artist, name)

      if (download):
         # Download the song
         print "Downloading: %s - \"%s\"" % (artist, name)
         f = urllib2.urlopen(track_url)
         with open("playlists/%s/%s - %s.mp3" % (mix_name, artist, name),
                  "w+") as song:
            song.write(f.read())

      # Notify 8tracks that the song is being played
      api_call("sets/%s/report" % play_token, mix_id=mix_id, track_id=track_id)

      # Queue the song via mpc
      os.system("mpc add \"%s\" 1>/dev/null" % track_url)
      os.system("mpc play 1>/dev/null")

      # If we're at the end of the mix finish up
      if song_info['set']['at_end']:
         print "Finished playing %s" % mix_name
         break
