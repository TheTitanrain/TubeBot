# TubeBot

Telegram bot for download audio from youtube video.

### How do I get set up? ###

* Configuration:  
File Config.py:  
DEBUG_ = True # for debug - true, for production - false  
if DEBUG_:  
    token = '' # debug bot token  
else:  
    token = '' # production bot token  
    botan_key = ''  
 
* Dependencies:  
  * Moviepy:    
  http://zulko.github.io/moviepy/    
  <code>pip install moviepy</code>    
  * Python implementation for the Telegram Bot API:    
  https://github.com/eternnoir/pyTelegramBotAPI    
  <code>pip install pyTelegramBotAPI</code>  
  * ffmpeg:  
  http://ffmpeg.org/download.html  
  Copy ffmpeg.exe to script directory.  
  * pytube  
  https://github.com/nficano/pytube/archive/master.zip  
  <code>python \pytube-master\setup.py install</code>
