import os
import yt_dlp
import discord
import shutil
import queue

from asyncio import Lock
from discord.ext import commands, tasks
from config import TOKEN

intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.listening, name="/play")

def move_file(source_path, destination_directory):
    try:
        # Полный путь к целевой директории
        destination_path = os.path.join(destination_directory, os.path.basename(source_path))

        # Перемещаем файл
        shutil.move(source_path, destination_path)

        print(f'Файл успешно перемещен в: {destination_path}')
    except Exception as e:
        print(f'Произошла ошибка при перемещении файла: {e}')


bot = commands.Bot(command_prefix="/", intents=intents, activity=activity, status=discord.Status.idle)

server, server_id, channel_name = None, None, None

domains = ["https://youtube.com", "http://youtube.com", "https://youtu.be/", "http://youtu.be/", "http://soundcloud.com/", "https://soundcloud.com/"]

# Создаем словарь для хранения очередей по гильдиям
queues = {}

# Создаем блокировку для безопасного доступа к очереди
queue_locks = {}

async def check_domains(link):
    for x in domains:
        if link.startswith(x):
            return True
    return False


@bot.event
async def on_ready():
    print("bot is online!")

async def play_next(ctx, curr_queue):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if not curr_queue.empty():
        next_source = curr_queue.get()
        await play_source(ctx, voice, next_source, curr_queue)
    else:
        await ctx.send('Очередь пуста. Воспроизведение завершено.')

async def play_source(ctx, voice, source, curr_queue):
    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': os.path.realpath('YOUR_FFMPEG.EXE_PATH'), 
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }
        ]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([source])
    for file in os.listdir(os.getcwd()):
        if file.endswith('mp3'):
            os.rename(file, 'song.mp3')
            move_file('song.mp3', f'{os.getcwd()}\\music\\')

    voice.play(discord.FFmpegPCMAudio(executable='YOUR_FFMPEG.EXE_PATH', source=f'{os.getcwd()}\\music\\song.mp3'), after=lambda e: bot.loop.create_task(play_next(ctx, curr_queue)))

        
@bot.command(name='play')
async def play(ctx, *, command = None):
    """Проигрывает музыку по ссылке"""
    global server, server_id, channel_name
    author = ctx.author
    if command == None:
        server = ctx.guild
        channel_name = author.voice.channel_name
        voice_channel = discord.utils.get(server.voice_channels, name = channel_name)
    params = command.split(' ')
    match(len(params)):
        case 1:
            sourse = params[0]
            server = ctx.guild
            channel_name = author.voice.channel.name
            voice_channel = discord.utils.get(server.voice_channels, name = channel_name)
            print("param 1")
        case 3:
            server_id, voice_id, sourse = params[0], params[1], params[2]
            try:
                server_id, voice_id = int(server_id), int(voice_id)
            except:
                await ctx.channel.send(f'{author.mention}, id сервера или войса должно быть целочисленным!')
                return
            print("param 3")
            server = bot.get_guild(server_id)
            voice_channel = discord.utils.get(server.voice_channels, id = voice_id)
        case default:
            await ctx.channel.send(f'{author.mention} команда некорректна!')
            return
        
    voice = discord.utils.get(bot.voice_clients, guild = server)
    
    if voice is None:
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild = server)
    

    if sourse == None:
        pass
    elif sourse.startswith("http"):
        if not check_domains(sourse):
            await ctx.channel.send(f'{author.mention} ссылка некорректна!')
            return
        
        song_there = os.path.isfile(f'{os.getcwd()}\\music\\song.mp3')
        
        try:
            if song_there:
                os.remove(f'{os.getcwd()}\\music\\song.mp3')
        except PermissionError:
            pass
        
        # Получаем или создаем очередь для текущей гильдии
        queue_lock = queue_locks.setdefault(ctx.guild.id, Lock())
        async with queue_lock:
            curr_queue = queues.setdefault(ctx.guild.id, queue.Queue())

            # Добавляем трек в очередь
            curr_queue.put(sourse)

            await ctx.send(f'Tрек добавлен в очередь. В очереди сейчас {curr_queue.qsize()} треков.')

            # Если бот не воспроизводит ничего, запускаем воспроизведение
            if not voice.is_playing():
                await play_next(ctx, curr_queue)
        
    else:
        voice.play(discord.FFmpegPCMAudio(executable='YOUR_FFMPEG.EXE_PATH', source=f'{os.getcwd()}\\music\\{sourse}'))
    
@bot.command(name='skip')
async def skip(ctx):
    """Позволяет пропустить текущий трек из очереди"""
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        await ctx.send('Текущий трек пропущен.')
        voice.stop()
    else:
        await ctx.send('Нет активного воспроизведения.')
    
    
@bot.command(name='leave')
async def leave(ctx):
    """Заставляет бота выйти из войса"""
    global server, channel_name
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_connected():
        await voice.disconnect()
    else:
        await ctx.channel.send(f'{ctx.author.mention}, бот отключен.')
        
@bot.command(name='pause')
async def pause(ctx):
    """Останавливает музыку"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.channel.send(f'{ctx.author.mention}, трек приостановлен.')
    
@bot.command(name='resume')
async def resume(ctx):
    """Воспроизводит музыку"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.channel.send(f'{ctx.author.mention}, трек играет дальше.')
                           
@bot.command(name='stop')
async def stop(ctx):
    """Останавливает текущее проигрывание трека"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    voice.stop()    
        
        
    

bot.run(TOKEN)