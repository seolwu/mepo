from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, DEBUG_SEPERATOR

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
public = supabase.schema('public')

async def insert_temp(id:int):
  try:
    data = { 'id': id }
    public.table('temp').upsert(data).execute()
  except Exception as err:
    print('[insert_temp] Failed to add row in temp', err, sep=DEBUG_SEPERATOR)

async def delete_channel(server_id:int, channel_id:str):
  try:
    table = public.table('channels')
    response = table.delete().eq('server_id', server_id).eq('channel_id', channel_id).execute()
    print('[delete_channel] The channel has been deleted', response, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[delete_channel] Failed to delete channel', err, sep=DEBUG_SEPERATOR)

async def insert_channel(data:dict):
  try:
    table = public.table('channels')
    response = table.insert(data).execute()
    print(f'[create_channel] A new channel {data.get('channel_name')} has been created', response, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[create_channel] Failed to create in channel', err, sep=DEBUG_SEPERATOR)

async def update_channel(server_id:int, channel_id:int, channel_name:str):
  try:
    table = public.table('channels')
    qeury = table.select()
    req = qeury.eq('server_id', server_id).eq('channel_id', channel_id) #.eq('channel_name', old_channel_name)
    channels = req.execute()
    if len(channels.data) > 0:
      channel = channels.data.pop(0)
      data = {
        'channel_id': channel_id,
        'channel_name': channel_name,
        'server_id': channel.get('server_id'),
        'created_at': channel.get('created_at'),
      }
      response = table.update(data).eq('channel_id', channel_id).execute()
      print('[update_channel] Channel update was successful', response, sep=DEBUG_SEPERATOR)
    else:
      print('[update_channel] The channel does not exist', channels, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[update_channel] Failed to update channel', err, sep=DEBUG_SEPERATOR)

async def check_version(server_id:int, channel_id:int):
  version = -1
  try:
    table = public.table('lit')
    query = table.select()
    messages = query.eq('server_id', server_id).eq('channel_id', channel_id).execute()
    if len(messages.data):
      for data in messages.data:
        if version < data.get('version'):
          version = data.get('version')
    print('[check_lit] Returns the version of the message', version, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[check_lit] Failed to return version of message', err, sep=DEBUG_SEPERATOR)
  return version

async def send_lit(data:dict):
  try:
    table = public.table('lit')
    response = table.insert(data).execute()
    print('[send_lit] Message data has been sent', response, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[send_lit] Failed to send message data', err, sep=DEBUG_SEPERATOR)

async def get_all_lits(server_id:int, channel_id:int):
  lits: any
  try:
    table = public.table('lit')
    query = table.select()
    lits = query.eq('server_id', server_id).eq('channel_id', channel_id).execute()
    print('[get_lit] Successfully fetched lit data', lits, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[get_lit] Failed to fetch lit data', err, sep=DEBUG_SEPERATOR)
  return lits

async def get_lit_by_version(version:int, server_id:int, channel_id:int):
  lit: any
  try:
    table = public.table('lit')
    query = table.select()
    lit = query.eq('version', version).eq('server_id', server_id).eq('channel_id', channel_id).execute()
    print('[get_lit] Successfully fetched lit data', lit, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[get_lit] Failed to fetch lit data', err, sep=DEBUG_SEPERATOR)
  return lit

async def delete_lit(server_id:int, message_id:int):
  try:
    table = public.table('lit')
    response = table.delete().eq('server_id', server_id).eq('message_id', message_id).execute()
    if len(response.data):
      print('[delete_lit] lit data in channel has been deleted', response, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[delete_lit] Failed to remove lit data', err, sep=DEBUG_SEPERATOR)

async def delete_lits(server_id:int, channel_id:int):
  try:
    table = public.table('lit')
    response = table.delete().eq('server_id', server_id).eq('channel_id', channel_id).execute()
    print('[delete_lit] All lit data in channel has been deleted', response, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[delete_lit] Failed to remove lit data', err, sep=DEBUG_SEPERATOR)

async def upsert_post(data:dict):
  success = False
  try:
    table = public.table('posts')
    response = table.upsert(data).execute()
    success = True
    print('[upsert_post] The post has been uploaded', response, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[upsert_post] Failed to upload post', err, sep=DEBUG_SEPERATOR)
  return success

# /post rem [channel_id?]
async def delete_post(channel_id:int, created_at:str):
  try:
    table = public.table('posts')
    query = table.delete()
    response = query.eq('id', channel_id).eq('created_at', created_at).execute()
    print('[delete_post] The post has been deleted', response, sep=DEBUG_SEPERATOR)
  except Exception as err:
    print('[delete_post] Failed to delete post', err, sep=DEBUG_SEPERATOR)
