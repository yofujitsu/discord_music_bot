import os
import yt_dlp
import discord
import shutil
import queue

from server import keep_alive
from asyncio import Lock
from discord.ext import commands, tasks
from discord import app_commands
from discord import Interaction
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


ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
    'executable': f'{os.getcwd()}\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe',  
    'probe_path': f'{os.getcwd()}\\ffmpeg-master-latest-win64-gpl\\bin\\ffprobe.exe',  
}

bot = commands.Bot(command_prefix="/", intents=intents, activity=activity, status=discord.Status.idle, ffmpeg_options=ffmpeg_options)

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
    await bot.tree.sync()
    print("bot is online!")

async def play_next(ctx: Interaction, curr_queue: queue):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if not curr_queue.empty():
        next_source = curr_queue.get()
        await play_source(ctx, voice, next_source, curr_queue)
    else:
        await ctx.response.send_message('Очередь пуста. Воспроизведение завершено.')

async def play_source(ctx: Interaction, voice: None, source: None, curr_queue: queue):
    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': os.path.realpath(f'{os.getcwd()}\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe'), 
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

    voice.play(discord.FFmpegPCMAudio(executable=f'{os.getcwd()}\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe', source=f'{os.getcwd()}\\music\\song.mp3'), after=lambda e: bot.loop.create_task(play_next(ctx, curr_queue)))

        
@bot.tree.command(name='play', description='Проигрывает музыку по ссылке')
async def play(ctx: Interaction, *, command: str = None):
    """Проигрывает музыку по ссылке"""
    global server, server_id, channel_name
    author = ctx.author if hasattr(ctx, 'author') else ctx.user
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

            await ctx.response.send_message(f'Tрек добавлен в очередь. В очереди сейчас {curr_queue.qsize()} треков.')

            # Если бот не воспроизводит ничего, запускаем воспроизведение
            if not voice.is_playing():
                await play_next(ctx, curr_queue)
        
    else:
        voice.play(discord.FFmpegPCMAudio(executable=f'{os.getcwd()}\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe', source=f'{os.getcwd()}\\music\\{sourse}'))
    
@bot.tree.command(name='skip', description='Позволяет пропустить текущий трек из очереди')
async def skip(ctx: Interaction):
    """Позволяет пропустить текущий трек из очереди"""
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        await ctx.response.send_message('Текущий трек пропущен.')
        voice.stop()
    else:
        await ctx.response.send_message('Нет активного воспроизведения.')
    
    
@bot.tree.command(name='leave', description='Заставляет бота выйти из войса')
async def leave(ctx: Interaction):
    """Заставляет бота выйти из войса"""
    global server, channel_name
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_connected():
        await voice.disconnect()
        await ctx.response.send_message(f'{ctx.user.mention}, бот отключен.')
    else:
        await ctx.response.send_message(f'{ctx.user.mention}, бот отключен.')
        
@bot.tree.command(name='pause', description='Останавливает музыку')
async def pause(ctx: Interaction):
    """Останавливает музыку"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_playing():
        voice.pause()
        await ctx.response.send_message(f'{ctx.user.mention}, трек приостановлен.')
    else:
        await ctx.response.send_message(f'{ctx.user.mention}, трек приостановлен.')
    
@bot.tree.command(name='resume', description='Воспроизводит музыку')
async def resume(ctx: Interaction):
    """Воспроизводит музыку"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_paused():
        voice.resume()
        await ctx.response.send_message(f'{ctx.user.mention}, трек играет дальше.')
    else:
        await ctx.response.send_message(f'{ctx.user.mention}, трек играет дальше.')
                           
@bot.tree.command(name='stop', description='Останавливает текущее проигрывание трека')
async def stop(ctx: Interaction):
    """Останавливает текущее проигрывание трека"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    voice.stop()
    await ctx.response.send_message(f'{ctx.user.mention}, проигрывание остановлено.')    
        
        
    
# keep_alive()
bot.run(TOKEN)