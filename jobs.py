import uuid
import asyncio
import schedule
from database import insert_temp

async def job():
  await insert_temp(uuid.uuid4().int)

async def schedule_jobs():
  schedule.every().day.at('00:00').do(lambda: asyncio.create_task(job()))

  while True:
    schedule.run_pending()
    await asyncio.sleep(1)
