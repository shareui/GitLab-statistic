import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
# local modules
from src.config import Config
from src.gitlab_service import GitLabService
from src.telegram_service import TelegramService
from src.commands import registerCommands

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = None
bot = None
dp = None
scheduler = None
gitlab_service = None
telegram_service = None

async def healthCheck(request):
    return web.Response(text="OK", status=200)

async def startHealthCheckServer():
    app = web.Application()
    app.router.add_get('/', healthCheck)
    app.router.add_get('/health', healthCheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', config.health_check_port)
    await site.start()
    logger.info(f"Health check server started on port {config.health_check_port}")
    return runner

async def scheduledPostStats():
    logger.info("Running scheduled GitLab stats check...")
    try:
        markdownMessage = await gitlab_service.getStats()
        logger.info("GitLab stats collected successfully, sending to Telegram...")
        await telegram_service.sendOrEditMessage(markdownMessage)
        
        job = scheduler.get_job('gitlab_stats_job')
        if job:
            logger.info(f"Next scheduled run: {job.next_run_time}")
    except Exception as e:
        logger.error(f"Failed to send/edit message: {e}", exc_info=True)

async def main():
    global config, bot, dp, scheduler, gitlab_service, telegram_service
    
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        exit(1)
    
    if config.telegram_bot_token == "yourBotToken" or config.gitlab_private_token == "GitLabprivatetoken":
        logger.error("!!! WARNING: Replace placeholder tokens in configuration file !!!")
    
    bot = Bot(token=config.telegram_bot_token)
    dp = Dispatcher()
    scheduler = AsyncIOScheduler()
    
    gitlab_service = GitLabService(config)
    telegram_service = TelegramService(bot, config)
    
    logger.info("Starting bot and scheduler...")
    healthRunner = await startHealthCheckServer()
    
    registerCommands(dp)
    
    firstRunTime = datetime.now() + timedelta(seconds=10)
    scheduler.add_job(
        scheduledPostStats,
        trigger='interval',
        hours=config.schedule_interval_hours,
        id='gitlab_stats_job',
        next_run_time=firstRunTime,
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Scheduler started. Checking every {config.schedule_interval_hours} hours.")
    
    job = scheduler.get_job('gitlab_stats_job')
    if job:
        logger.info(f"First run scheduled at: {job.next_run_time}")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Shutting down bot...")
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await healthRunner.cleanup()
        logger.info("Bot shutdown complete.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Bot stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"Critical error during bot startup: {e}")