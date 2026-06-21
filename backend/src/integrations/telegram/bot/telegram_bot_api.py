from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramUnauthorizedError
from aiogram.types import (
    BotCommand,
    LinkPreviewOptions,
    MenuButtonWebApp,
    Message,
    User,
    UserProfilePhotos,
    WebAppInfo,
)

from loggers import get_logger

logger = get_logger(__name__)


class TelegramBotAPIService:
    """
    Infrastructure Service for interacting with the Telegram Bot API.
    Uses 'aiogram' v3 library under the hood.

    This service is stateless regarding the bot instance; it requires the token
    to be passed for every operation. This is necessary for a multi-tenant
    architecture where we manage thousands of different bots.
    """

    async def _get_bot_instance(self, token: str) -> Bot:
        """
        Creates a temporary Bot instance with default properties.
        """
        return Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

    async def _close_bot_session(self, bot: Bot) -> None:
        """
        Safely closes the bot session to prevent unclosed client connection warnings.
        """
        try:
            await bot.session.close()
        except Exception as e:
            logger.warning("Error closing bot session: %s", e)

    async def get_me(self, token: str) -> User | None:
        """
        Validates the token and returns basic bot information.
        Useful for the initial setup of the bot.

        Args:
            token: The raw Telegram Bot Token.

        Returns:
            User object: Bot information (id, first_name, username) or None if invalid.
        """
        bot = await self._get_bot_instance(token)
        try:
            user = await bot.get_me()
            return user
        except TelegramUnauthorizedError:
            logger.warning("Invalid token provided for get_me check.")
            return None
        except TelegramAPIError as e:
            logger.error("Telegram API Error during get_me: %s", e)
            return None
        finally:
            await self._close_bot_session(bot)

    async def get_profile_photos(
        self, token: str, user_id: int, offset: int = 0, limit: int = 10
    ) -> UserProfilePhotos | None:
        """
        Retrieves the profile photos of a Telegram user.

        Args:
            token: The raw Telegram Bot Token.
            user_id: The Telegram user ID.
            offset: Sequential number of the first photo to be returned.
            limit: Maximum number of photos to be returned.

        Returns:
            UserProfilePhotos: The profile photos object, or None if failed.
        """
        bot = await self._get_bot_instance(token)
        try:
            photos = await bot.get_user_profile_photos(
                user_id=user_id, offset=offset, limit=limit
            )
            return photos
        except TelegramAPIError as e:
            logger.error("Failed to get profile photos for user %s: %s", user_id, e)
            return None
        finally:
            await self._close_bot_session(bot)

    async def set_webhook(self, token: str, url: str, secret_token: str) -> bool:
        """
        Sets the webhook for the bot to point to our backend.

        Args:
            token: The raw Telegram Bot Token.
            url: The full HTTPS URL of our webhook endpoint.
            secret_token: A secret string used to validate incoming payloads (X-Telegram-Bot-Api-Secret-Token).

        Returns:
            bool: True if successful, False otherwise.
        """
        bot = await self._get_bot_instance(token)
        try:
            # We drop pending updates to prevent flooding the backend with old messages upon connection
            await bot.set_webhook(
                url=url,
                drop_pending_updates=True,
                secret_token=secret_token,
                allowed_updates=["message", "edited_message", "callback_query"],
            )
            logger.info("Webhook set successfully for bot.")
            return True
        except TelegramAPIError as e:
            logger.error("Failed to set webhook: %s", e)
            return False
        finally:
            await self._close_bot_session(bot)

    async def delete_webhook(self, token: str) -> bool:
        """
        Removes the webhook integration.
        """
        bot = await self._get_bot_instance(token)
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            return True
        except TelegramAPIError as e:
            logger.error("Failed to delete webhook: %s", e)
            return False
        finally:
            await self._close_bot_session(bot)

    async def send_message(
        self,
        token: str,
        chat_id: int | str,
        text: str,
        reply_to_message_id: int | None = None,
        disable_link_preview: bool = False,
    ) -> Message | None:
        """
        Sends a text message to a specific chat.

        Args:
            token: Decrypted raw bot token.
            chat_id: Target Telegram chat ID.
            text: Message content (supports HTML by default).
            reply_to_message_id: Optional ID of the message to reply to.
            disable_link_preview: Whether to hide link previews.

        Returns:
            dict: The sent message object as a dict, or None if failed.
        """
        bot = await self._get_bot_instance(token)
        try:
            link_preview = (
                LinkPreviewOptions(is_disabled=True) if disable_link_preview else None
            )

            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=reply_to_message_id,
                link_preview_options=link_preview,
            )
            return message
        except TelegramAPIError as e:
            logger.error("Failed to send message to chat %s: %s", chat_id, e)
            return None
        finally:
            await self._close_bot_session(bot)

    async def set_my_commands(self, token: str, commands: dict[str, str]) -> bool:
        """
        Sets the bot's menu commands.

        Args:
            token: Raw token.
            commands: Dict where key is command (e.g., 'start') and value is description.
        """
        bot = await self._get_bot_instance(token)
        try:
            bot_commands = [
                BotCommand(command=cmd, description=desc)
                for cmd, desc in commands.items()
            ]
            is_success = await bot.set_my_commands(commands=bot_commands)
            if is_success:
                logger.info("Bot commands set successfully.")
                return True
            return False
        except TelegramAPIError as e:
            logger.error("Failed to set bot commands: %s", e)
            return False
        finally:
            await self._close_bot_session(bot)

    async def set_chat_menu_button(
        self, token: str, chat_id: int | str, url: str, text: str
    ) -> bool:
        """
        Sets a custom menu button for a specific chat.

        Args:
            token: Raw token.
            chat_id: Target Telegram chat ID.
            url: The URL of the web app to open when the menu button is pressed.
            text: The text to display on the menu button.
        """
        bot = await self._get_bot_instance(token)
        try:
            menu_button = MenuButtonWebApp(
                text=text,
                web_app=WebAppInfo(url=url),
            )
            is_success = await bot.set_chat_menu_button(
                chat_id=int(chat_id), menu_button=menu_button
            )
            if is_success:
                logger.info("Chat menu button set successfully.")
                return True
            return False
        except TelegramAPIError as e:
            logger.error("Failed to set chat menu button for chat %s: %s", chat_id, e)
            return False
        finally:
            await self._close_bot_session(bot)
