"""Message handler cog for Discord bot."""
import discord
from discord.ext import commands
from services import LLMService
from config import Config
from utils.logger import get_logger
from utils.rate_limit import RateLimiter


logger = get_logger(__name__)


class MessageHandlerCog(commands.Cog):
    """Handles message events and LLM interactions."""

    def __init__(self, bot: commands.Bot):
        """
        Initialize the cog.
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.llm_service = LLMService()
        
        # Initialize rate limiters
        self.user_rate_limiter = RateLimiter(
            Config.RATE_LIMIT_CALLS_PER_USER_PER_MINUTE
        )
        self.guild_rate_limiter = RateLimiter(
            Config.RATE_LIMIT_CALLS_PER_GUILD_PER_MINUTE
        )

        logger.info("MessageHandlerCog initialized")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Handle incoming messages.
        
        Args:
            message: Discord message object
        """
        # Ignore bot's own messages
        if message.author == self.bot.user:
            return

        # Check if bot was mentioned
        if self.bot.user not in message.mentions:
            return

        try:
            await self._handle_mentioned_message(message)
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            await self._send_error_message(message, str(e))

    async def _handle_mentioned_message(self, message: discord.Message) -> None:
        """
        Process a message where the bot was mentioned.
        
        Args:
            message: Discord message object
        """
        # Extract prompt by removing bot mention
        cleaned_prompt = self._extract_prompt(message.content, self.bot.user.id)

        if not cleaned_prompt:
            await message.channel.send(
                f"Hello {message.author.mention}! I am online 🤖\nAsk me anything."
            )
            return

        # Check rate limits
        user_id = str(message.author.id)
        guild_id = str(message.guild.id) if message.guild else "dm"

        if not self._check_rate_limits(message, user_id, guild_id):
            return

        # Show typing indicator
        if Config.TYPING_INDICATOR_ENABLED:
            async with message.channel.typing():
                response = await self._get_llm_response(cleaned_prompt)
        else:
            response = await self._get_llm_response(cleaned_prompt)

        # Send response
        await self._send_response(message, response)

    def _extract_prompt(self, content: str, bot_id: int) -> str:
        """
        Extract user prompt from message by removing bot mention.
        
        Args:
            content: Message content
            bot_id: Bot's user ID
        
        Returns:
            Cleaned prompt string
        """
        # Remove mention formats: <@bot_id> and <@!bot_id>
        cleaned = content.replace(f"<@{bot_id}>", "").replace(
            f"<@!{bot_id}>", ""
        ).strip()
        return cleaned

    def _check_rate_limits(
        self, message: discord.Message, user_id: str, guild_id: str
    ) -> bool:
        """
        Check rate limits for user and guild.
        
        Args:
            message: Discord message object
            user_id: User ID string
            guild_id: Guild ID string
        
        Returns:
            True if allowed, False if rate limited
        """
        if not Config.RATE_LIMIT_ENABLED:
            return True

        # Check user rate limit
        if not self.user_rate_limiter.is_allowed(user_id):
            cooldown = self.user_rate_limiter.get_cooldown_seconds(user_id)
            logger.warning(f"User {user_id} rate limited (cooldown: {cooldown}s)")
            return False

        # Check guild rate limit
        if not self.guild_rate_limiter.is_allowed(guild_id):
            cooldown = self.guild_rate_limiter.get_cooldown_seconds(guild_id)
            logger.warning(f"Guild {guild_id} rate limited (cooldown: {cooldown}s)")
            return False

        return True

    async def _get_llm_response(self, prompt: str) -> str:
        """
        Get response from LLM service.
        
        Args:
            prompt: User prompt
        
        Returns:
            LLM response text
        """
        return await self.bot.loop.run_in_executor(None, self.llm_service.ask, prompt)

    async def _send_response(self, message: discord.Message, response: str) -> None:
        """
        Send LLM response to Discord channel.
        
        Args:
            message: Original Discord message
            response: LLM response text
        """
        # Truncate if necessary
        if len(response) > Config.MAX_MESSAGE_LENGTH:
            response = (
                response[: Config.MAX_MESSAGE_LENGTH - 4] + "..."
            )
            logger.info(
                f"Response truncated from {len(response)} to {Config.MAX_MESSAGE_LENGTH} characters"
            )

        content = f"{message.author.mention}\n{response}"
        await message.channel.send(content)

    async def _send_error_message(self, message: discord.Message, error: str) -> None:
        """
        Send error message to Discord channel.
        
        Args:
            message: Original Discord message
            error: Error message text
        """
        # Truncate error message for safety
        error_display = error[: Config.MAX_MESSAGE_LENGTH - 50]
        content = f"{message.author.mention}\n❌ Error: {error_display}"
        try:
            await message.channel.send(content)
        except Exception as e:
            logger.error(f"Failed to send error message: {str(e)}")


async def setup(bot: commands.Bot) -> None:
    """
    Load the cog into the bot.
    
    Args:
        bot: Discord bot instance
    """
    await bot.add_cog(MessageHandlerCog(bot))
