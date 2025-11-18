"""Main entry point for Andy AI Discord Bot."""
import asyncio
import discord
from discord.ext import commands
from config import Config
from utils.logger import setup_logger, get_logger


# Setup logging
logger = setup_logger(__name__)


class AndyAIBot(commands.Bot):
    """Main Discord bot class."""

    def __init__(self, *args, **kwargs):
        """Initialize bot with configuration."""
        super().__init__(*args, **kwargs)
        logger.info("AndyAIBot instance created")

    async def setup_hook(self) -> None:
        """Load cogs and initialize bot."""
        logger.info("Setting up bot...")
        try:
            await self.load_extension("cogs.message_handler")
        except Exception as e:
            logger.error(f"Failed to load cog: {e}", exc_info=True)
            raise
        logger.info("Cogs loaded successfully")

    async def on_ready(self) -> None:
        """Called when bot is ready and connected."""
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info(f"Config: {Config.to_dict()}")

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Handle bot errors."""
        logger.error(f"Error in {event}: {args}, {kwargs}", exc_info=True)


def create_bot() -> AndyAIBot:
    """
    Create and configure the bot instance.
    
    Returns:
        Configured AndyAIBot instance
    """
    intents = discord.Intents.default()
    intents.message_content = True

    bot = AndyAIBot(
        command_prefix=commands.when_mentioned_or(Config.COMMAND_PREFIX),
        case_insensitive=Config.CASE_INSENSITIVE,
        intents=intents,
    )

    return bot


async def main() -> None:
    """
    Main entry point for the bot.
    
    Raises:
        ValueError: If required configuration is missing
    """
    # Validate configuration
    Config.validate()

    # Create bot
    bot = create_bot()

    # Run bot
    logger.info("Starting bot...")
    async with bot:
        await bot.start(Config.DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise