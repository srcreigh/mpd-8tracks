mpd-8tracks
===========

Uses mpc to queue tracks from 8tracks mixes to mpd.

Usage
-----

1. Clone this repo
2. Head on over to http://8tracks.com/developers to register as a developer and get an API key.
3. Voila! That should work. You can enter your API key via stdin, or put it in a ```config.json``` file
as follows:

```json
{
  "apikey": "abcdef123456890abcdef1234"
}
```

Make sure mpd is running and that you have mpc installed. There are further 
instructions/information in the script itself.

