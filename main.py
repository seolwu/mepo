import time
import datetime
import discord
from discord import MessageType, option
from discord.ext import commands

from config import BOT_TOKEN, NUMBER_MAX_INTERGER, CATEGORY_NAME, DEBUG_SEPERATOR
from jobs import schedule_jobs
from database import insert_channel, update_channel, delete_channel, check_version, send_lit, get_all_lits, get_lit_by_version, delete_lit, delete_lits, upsert_post, delete_post

intents = discord.Intents.default()
intents.presences = True
intents.voice_states = False
intents.message_content = True

bot = discord.Bot(intents=intents)
post = bot.create_group('post', '게시물을 만들고 관리합니다')
# config = bot.create_group('config', '')

async def create_category(ctx, name:str=CATEGORY_NAME):
  guild = ctx.guild
  try:
    category = discord.utils.get(guild.categories, name=name)
    if not category:
      category = await guild.create_category(name)
      await ctx.respond('초기화 되었습니다.', ephemeral=True)
      print(f'[post_category] A new category {name.upper()} has been created')
    else:
      await ctx.respond('이미 초기화되었습니다.', ephemeral=True)
      print(f'[post_category] The category {name.upper()} already exists')
  except Exception as err:
    await ctx.respond('초기화에 실패했습니다.', ephemeral=True)
    print('[create_category] Failed to create category', err, sep=DEBUG_SEPERATOR)
  
async def create_channel_from_category(ctx, name:str, category_name:str=CATEGORY_NAME):
  guild = ctx.guild
  try:
    category = discord.utils.get(guild.categories, name=category_name)
    channel = await guild.create_text_channel(name, category=category)
    await ctx.respond('채널이 생성되었습니다.', ephemeral=True)
    print(f'[post_channel] A new channel {channel.name.upper()} has been created')
  except Exception as err:
    await ctx.respond('채널 생성에 실패했습니다.', ephemeral=True)
    print('[create_channel] Failed to create channel', err, sep=DEBUG_SEPERATOR)

async def send_message(message:discord.Message):
  server_id = message.guild.id
  channel_id = message.channel.id
  version = await check_version(server_id, channel_id)
  data = {
    'server_id': server_id,
    'channel_id': channel_id,
    'message_id': message.id,
    'user_id': message.author.id,
    'version': int(version) + 1,
  }
  await send_lit(data)

async def update_post(message, channel, update: datetime.datetime):
  lits = await get_all_lits(channel.guild.id, channel.id)
  contributors = []
  for lit in lits.data:
    user = await channel.guild.fetch_member(lit['user_id'])
    contributor = {
      'name': user.display_name,
      'avatarUrl': user.display_avatar.with_size(128).url,
    }
    contributors.append(contributor)
  data = {
    'id': channel.id,
    'title': channel.name,
    'description': channel.topic if channel.topic else '',
    'content': message.content,
    'contributors': contributors,
    'created_at': date_to_ts(channel.created_at),
    'last_update': date_to_ts(update),
  }
  res = await upsert_post(data)
  return res

async def unpin_all(pins):
  if len(pins):
    for msg in pins:
      if msg:
        await msg.unpin()
    return True
  else:
    return False

async def unpin_except_latest(pins):
  if len(pins):
    lit = pins.pop(0)
    for msg in pins:
      if msg:
        await msg.unpin()
    return [lit, pins]
  else:
    return [None, pins]

def date_to_ts(date:datetime.datetime, timezone=datetime.timezone.utc):
  timestamp = date.replace(tzinfo=timezone).isoformat()
  return timestamp

@bot.event
async def on_ready():
  print(f'[login] {bot.user}')
  await bot.change_presence(
    status=discord.Status.online,
    activity=discord.Activity(
      type=discord.ActivityType.watching,
      name=CATEGORY_NAME.lower()))
  bot.loop.create_task(schedule_jobs())

@bot.event
async def on_message(message):
  if not isinstance(message.channel, discord.channel.TextChannel): return
  if message.type == MessageType.default:
    if not message.channel.category: return
    if message.channel.category.name == CATEGORY_NAME:
      await send_message(message)
  elif message.type == MessageType.pins_add:
    if not message.channel.category: return
    if message.channel.category.name == CATEGORY_NAME:
      await message.delete()

@bot.event
async def on_raw_message_delete(payload):
  channel = bot.get_channel(payload.channel_id)
  if channel:
    category = channel.category
    if category and category.name == CATEGORY_NAME:
      await delete_lit(payload.guild_id, payload.message_id)
      await delete_post(payload.channel_id, date_to_ts(channel.created_at))

@bot.event
async def on_guild_channel_delete(channel):
  if not channel: return
  if not channel.category: return
  if channel.category.name == CATEGORY_NAME:
    server_id = channel.guild.id
    channel_id = channel.id
    await delete_channel(server_id, channel_id)
    await delete_lits(server_id, channel_id)
    await delete_post(channel_id, date_to_ts(channel.created_at))

@bot.event
async def on_guild_channel_create(channel):
  if not channel: return
  if not channel.category: return
  if channel.category.name == CATEGORY_NAME:
    data = {
      'channel_id': channel.id,
      'channel_name': channel.name,
      'server_id': channel.guild.id,
    }
    await insert_channel(data)

@bot.event
async def on_guild_channel_update(before, after):
  if before.id == after.id:
    await update_channel(after.guild.id, after.id, after.name)
  else:
    print('[update_db] The channel could not be updated because the ID was tampered with')

@bot.event
async def on_guild_channel_pins_update(channel, last_pin):
  category = discord.utils.get(channel.guild.categories, name=CATEGORY_NAME)
  if not channel.category or not category: return
  if channel.category_id == category.id:
    pins = await channel.pins()
    [msg, left_msgs] = await unpin_except_latest(pins)
    if len(left_msgs):
      print('[pins] Unpinned all pinned messages')
    if msg and last_pin:
      await update_post(msg, channel, last_pin)
    else:
      channel_id = channel.id
      created_at = date_to_ts(channel.created_at)
      await delete_post(channel_id, created_at)

@post.command(name='init', description='게시물을 등록하기 위한 기반을 구축합니다')
@commands.has_permissions(manage_guild=True)
async def post_init(ctx):
  if isinstance(ctx.channel, discord.channel.TextChannel):
    await create_category(ctx)
  
@post.command(name='new', description='게시물을 등록할 채널을 생성합니다')
@commands.has_permissions(manage_channels=True)
@option('title', description='게시물 및 채널에 사용할 제목을 입력하세요', required=True)
async def post_new(ctx, title:str):
  if isinstance(ctx.channel, discord.channel.TextChannel):
    category = discord.utils.get(ctx.guild.categories, name=CATEGORY_NAME)
    if category:
      await create_channel_from_category(ctx, title)

@post.command(name='update', description='게시물을 업데이트합니다')
@commands.has_permissions(manage_messages=True)
@commands.has_permissions(read_message_history=True)
@option('version', description=f'업데이트할 버전을 입력하세요', required=False)
async def post_update(ctx, version:int=-1):
  if isinstance(ctx.channel, discord.channel.TextChannel):
    category = discord.utils.get(ctx.guild.categories, name=CATEGORY_NAME)
    if category:
      if -1 > version:
        await ctx.respond('버전에는 음수가 포함될 수 없습니다.', ephemeral=True)
      elif version > NUMBER_MAX_INTERGER:
        await ctx.respond('최대치를 초과하여 업데이트할 수 없습니다.', ephemeral=True)
      else:
        lits = await get_all_lits(ctx.channel.guild.id, ctx.channel.id)
        lit:any|None = None
        if version == -1:
          sorted_lits = sorted(lits.data, key=lambda lit: lit['version'])
          lit = sorted_lits.pop()
        else:
          filtered_lits = list(filter(lambda lit: lit['version'] == version, lits.data))
          lit = filtered_lits.pop()
        msg = await ctx.fetch_message(lit['message_id'])
        if msg:
          if msg.pinned:
            await ctx.respond('이 버전은 이미 등록되었습니다.', ephemeral=True)
          else:
            await msg.pin()
            await ctx.respond('게시물을 성공적으로 업로드했습니다!', ephemeral=True)

@post.command(name='delete', description='게시물을 삭제합니다')
@commands.has_permissions(manage_messages=True)
async def post_delete(ctx):
  pins = await ctx.pins()
  if len(pins):
    unpinned = await unpin_all(pins)
    if unpinned:
      await ctx.respond('게시물이 삭제되었습니다.', ephemeral=True)
    else:
      await ctx.respond('게시물이 존재하지 않습니다.', ephemeral=True)

if BOT_TOKEN:
  bot.run(BOT_TOKEN)
