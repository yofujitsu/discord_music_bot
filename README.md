## Fully customizable discord music player bot
### This bot can play music from Youtube, Soundcloud and Deezer via links 
![image](https://github.com/yofujitsu/discord_music_bot/assets/78373273/eecd8127-e8b2-4316-baba-b66f063691fe)
### Commands list
![image](https://github.com/yofujitsu/discord_music_bot/assets/78373273/e592c2dc-3a3f-4d13-878b-bdcbbd8cc3d4)
## Features
![image](https://github.com/yofujitsu/discord_music_bot/assets/78373273/461d4d25-8a32-4b40-a88f-8247ac95d72c)
- playing music via links
- 320 kbps mp3
- queues for playlists
- commands for skip, resume, pause tracks
### If you want to customize this bot for your purposes u need:
- create application in [**Discord Developer Portal**](https://discord.com/developers/)
- Add application to your server
- Insert your bot's `TOKEN` into config.py
- Install `ffmpeg` from [official site](https://ffmpeg.org/)
- Replace `"YOUR_FFMPEG.MP3_PATH"` with your real ffmpeg.exe path in bot.py
- Install **Python 3.12.1** and Libraries via pip:
  ```
  pip install discord (to link with discord)
  pip install discord.py[voice] (to have ability for joining voice chat)
  pip install yt_dlp (for downloading the tracks)
  ```
- Add "music" folder in project (there will be your mp3's)
![image](https://github.com/yofujitsu/discord_music_bot/assets/78373273/dbf31937-8fb5-44a0-948d-22c83a25aa43)
- Run code in terminal `python bot.py`
### Also you can set your custom bot status, intents and activity in this string of code:
```
bot = commands.Bot(command_prefix="ANY PREFIX: !, /, -", intents=YOUR_INTENTS, activity=YOUR_ACTIVITY, status=YOUR_DISCORD_STATUS)
```
