import asyncio
import logging

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.postedMessageId = None
    
    async def sendNewMessage(self, markdownMessage):
        try:
            sentMessage = await asyncio.wait_for(
                self.bot.send_message(
                    chat_id=self.config.target_channel_id,
                    text=markdownMessage,
                    parse_mode="MarkdownV2"
                ),
                timeout=30.0
            )
            self.postedMessageId = sentMessage.message_id
            logger.info(f"New message sent with ID: {self.postedMessageId}")
        except asyncio.TimeoutError:
            logger.error("Timeout while sending new message")
        except Exception as sendError:
            logger.error(f"Failed to send new message: {sendError}")
    
    async def sendOrEditMessage(self, markdownMessage):
        targetMessageId = self.config.force_message_id if self.config.force_message_id != 0 else self.postedMessageId
        
        if targetMessageId:
            try:
                await asyncio.wait_for(
                    self.bot.edit_message_text(
                        chat_id=self.config.target_channel_id,
                        message_id=targetMessageId,
                        text=markdownMessage,
                        parse_mode="MarkdownV2"
                    ),
                    timeout=30.0
                )
                logger.info(f"Statistics message {targetMessageId} successfully updated.")
                if self.config.force_message_id == 0:
                    self.postedMessageId = targetMessageId
            except asyncio.TimeoutError:
                logger.error(f"Timeout while editing message {targetMessageId}")
                if self.config.force_message_id == 0:
                    await self.sendNewMessage(markdownMessage)
            except Exception as editError:
                logger.error(f"Failed to edit message {targetMessageId}: {editError}")
                if self.config.force_message_id != 0:
                    logger.error(f"Message with ID {self.config.force_message_id} not found or cannot be edited.")
                else:
                    await self.sendNewMessage(markdownMessage)
        else:
            await self.sendNewMessage(markdownMessage)