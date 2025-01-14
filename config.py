import os

BOT_TOKEN: str = os.environ.get('BOT_TOKEN')
SUPABASE_URL: str = os.environ.get('SUPABASE_URL')
SUPABASE_KEY: str = os.environ.get('SUPABASE_KEY')

CATEGORY_NAME: str = os.environ.get('CATEGORY_NAME')

NUMBER_MAX_INTERGER: int = 9007199254740991

DEBUG_SEPERATOR = '\n >> '