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
import xml.etree.ElementTree as ET
import xml.dom

def normalize(s):
   t = s.encode('ascii', 'ignore')
   return t.translate(None, "'/")

# Open the API developer key
api_key = open("8tracksdevkey.txt", 'r').readline()[:-1]

# Check for correct usage (i.e. that a url has been given)
if (len(sys.argv) != 2):
   print "ERR: Usage: python mpd8tracks [url to an 8tracks mix]"
   sys.exit(2)
else:
   mix_url = sys.argv[1]

# Check that MPD/MPC is working
if (os.system('mpc 1>/dev/null 2>/dev/null') != 0):
   print "ERR: MPD isn't running; please start mpd and run again"
   sys.exit(1)

# Set up mpd
os.system("mpc clear 1>/dev/null")
os.system("mpc consume on 1>/dev/null")

# Get the mix information, extract the mix id
query_url = "%s.xml?api_key=%s" % (mix_url, api_key)
mix_info = ET.fromstring(urllib2.urlopen(query_url).read())

for info in mix_info[0]:
   if info.tag == 'id':    mix_id = info.text
   if info.tag == 'name':  mix_name = normalize(info.text)

os.system("mkdir \"/home/shane/Music/8tracks/%s\" \
          1>/dev/null 2>/dev/null" % mix_name)

# Get the play token
query_url = "http://8tracks.com/sets/new.xml?api_key=%s" % api_key
play_token_info = ET.fromstring(urllib2.urlopen(query_url).read())
for n in play_token_info:
   if n.tag == 'play-token': play_token = n.text

song_info = ET.fromstring(urllib2.urlopen(query_url).read())

# Song playing loop
last_song = False
infos = []
while not last_song:

   # Load the next song
   query_url = "http://8tracks.com/sets/%s/next.xml" % play_token
   query_url += "?mix_id=" + mix_id
   query_url += "&api_key=" + api_key
   song_info = ET.fromstring(urllib2.urlopen(query_url).read())

   # Get relevant information and save it
   for i in song_info[0]:
      if i.tag == 'at-end' and i.text == 'true':
         last_song = True
         continue
      if i.tag == 'track':
         for j in i:
            if j.tag == 'id':          
               track_id = j.text
            elif j.tag == 'name':      
               name = normalize(j.text)
            elif j.tag == 'performer': 
               artist = normalize(j.text)
            elif j.tag == 'url':       
               track_url = j.text

   print "Enqueuing %s - \"%s\"" % (artist, name)

   # Notify 8tracks that the song is being played
   query_url = "http://8tracks.com/sets/%s/report.xml" % play_token
   query_url += "?mix_id=" + mix_id
   query_url += "&track_id=" + track_id
   query_url += "&api_key=" + api_key
   # note: do not need to save any information, just need to call the url
   urllib2.urlopen(query_url) 

   # Fix the url if necessary (https://api.soundcloud.com/foobarabc123 ones
   # don't work)
   if (track_url[:5] == "https"):
      track_url = "http" + track_url[:5]

   print "track url: %s" % track_url
   
   # Queue the song via mpc
   os.system("mpc add \"%s\" 1>/dev/null" % track_url)
   os.system("mpc play 1>/dev/null")

   infos.append((track_url, artist, name))
   
while True:
   foo = raw_input("Save songs for later? [yn]\n > ")
   if (foo == 'y'):
      os.system("mkdir music 2>/dev/null")
      os.system("mkdir music/%s 2>/dev/null" % mix_name)

      for url, artist, name in infos:
         
         f = urllib2.urlopen(url)
         print "Downloading " + artist + " - \"%s\"" % name
         with open("music/%s/%s - %s.m4a" \
                   % (mix_name, artist, name), "w+") as music:
            music.write(f.read())

      break
   elif (foo == 'n'): 
      break
