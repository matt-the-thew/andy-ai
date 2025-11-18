# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Discord Bot (main.py)                   │
│  - Initializes bot with configuration                       │
│  - Loads cogs                                               │
│  - Handles startup/shutdown                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐  ┌─────────────┐  ┌───────────┐
   │ Config  │  │ Logging     │  │ Cogs      │
   │ Module  │  │ Module      │  │           │
   └─────────┘  └─────────────┘  └─────┬─────┘
                                        │
                            ┌───────────┴────────────┐
                            │                        │
                    ┌───────▼──────────┐    ┌───────▼──────────┐
                    │ MessageHandler   │    │ (Future Cogs)    │
                    │ Cog              │    │                  │
                    │ - on_message()   │    │ - Custom commands│
                    │ - Rate limiting  │    │ - Events         │
                    │ - Error handling │    │ - Utilities      │
                    └────────┬─────────┘    └──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ LLMService       │
                    │ - ask()          │
                    │ - Retries        │
                    │ - Caching        │
                    │ - Error handling │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐        ┌──────────┐      ┌──────────┐
    │ Cache    │        │ OpenAI   │      │ Rate     │
    │ Module   │        │ API      │      │ Limiter  │
    │ (TTL)    │        │          │      │ Module   │
    └──────────┘        └──────────┘      └──────────┘
```

## Component Responsibilities

### Core Components

#### 1. **main.py** - Entry Point
- Creates AndyAIBot instance
- Loads Discord intents
- Configures command prefix
- Handles bot lifecycle events (on_ready, on_error)
- Manages async execution

#### 2. **config/settings.py** - Configuration
- Centralized settings management
- Environment variable loading
- Configuration validation
- Export non-sensitive config

#### 3. **services/llm_service.py** - OpenAI Integration
- Encapsulates OpenAI API interaction
- Implements retry logic with exponential backoff
- Manages response caching
- Handles all LLM-related errors

#### 4. **cogs/message_handler.py** - Discord Events
- Listens to message events
- Extracts prompts from mentions
- Enforces rate limits
- Manages typing indicators
- Sends responses back to Discord

### Utility Modules

#### 5. **utils/logger.py** - Structured Logging
- Configures console and file logging
- Implements log rotation
- Provides consistent formatting
- Supports multiple log levels

#### 6. **utils/cache.py** - Response Caching
- In-memory cache with TTL
- Generic cache entries
- Expiration handling
- Cache statistics

#### 7. **utils/rate_limit.py** - Rate Limiting
- Token bucket algorithm
- Per-key rate limiting
- Cooldown calculation
- Multiple rate limit tracking

## Data Flow

### Message Processing Flow

```
1. Discord sends message event
   │
2. MessageHandlerCog.on_message() triggered
   │
3. Check if bot was mentioned
   │
   └─ If no mention: ignore
   │
4. Extract prompt from message content
   │
5. Check rate limits
   │
   ├─ User rate limit exceeded? Send error
   ├─ Guild rate limit exceeded? Send error
   │
6. Show typing indicator
   │
7. Call LLMService.ask(prompt)
   │
   ├─ Check response cache
   │  │
   │  ├─ Cache hit? Return cached response
   │  │
   │  └─ Cache miss? Continue...
   │
8. Call OpenAI API (with retries and backoff)
   │
   ├─ Success? Cache response
   │
   ├─ Timeout/Connection error? Retry with backoff
   │
   ├─ API error? Log and return error to user
   │
   └─ After max retries? Raise RuntimeError
   │
9. Truncate response if necessary
   │
10. Send response to Discord channel
   │
11. Log success/failure
```

## Error Handling Strategy

### Layers of Error Handling

```
Discord Layer (Cog)
│
├─ Input validation (prompt not empty)
├─ Rate limit checks
├─ Try-catch around entire message handler
│
    LLMService Layer
    │
    ├─ Specific exception types
    ├─ Retry logic (3 attempts max)
    ├─ Exponential backoff (2^attempt)
    ├─ Timeout protection
    │
        OpenAI API Layer
        │
        ├─ APITimeoutError → Retry
        ├─ APIConnectionError → Retry
        ├─ APIError (401/403) → Fail fast
        ├─ Rate limit (429) → Retry with longer wait
        └─ Other errors → Log and fail gracefully
    │
    └─ Return error message or cached response

Response Layer (Cog)
│
└─ Catch any unexpected errors
   └─ Send error message to user
```

## Performance Characteristics

### Latency
- **First request**: 2-5 seconds (depends on OpenAI API)
- **Cached request**: <100ms
- **Rate limit check**: <1ms
- **Discord send**: ~1 second

### Memory
- **Idle memory**: ~50-100MB
- **Per cached response**: ~1KB average
- **Cache size limit**: Unbounded (consider adding max size)

### Network
- **API calls**: 1 call per unique prompt (with caching)
- **Discord API**: ~2-3 calls per message (read, send, edit)

## Extensibility

### Adding New Cogs

```python
# Create new file: cogs/my_feature.py

from discord.ext import commands

class MyFeatureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def my_command(self, ctx):
        await ctx.send("Response")

async def setup(bot):
    await bot.add_cog(MyFeatureCog(bot))
```

Then add to main.py:
```python
await self.load_cog("cogs.my_feature")
```

### Adding New Services

Follow the same pattern as LLMService:
1. Create `services/my_service.py`
2. Implement service class with proper error handling
3. Import in cogs that need it
4. Inject as dependency

### Adding Configurations

Update `config/settings.py`:
```python
class Config:
    MY_NEW_SETTING: str = os.getenv("MY_NEW_SETTING", "default_value")
```

## Testing Strategy

### Unit Tests
- **LLMService**: Mock OpenAI API, test retries and caching
- **Utils**: Test cache TTL, rate limiter logic
- **Config**: Test validation and env var loading

### Integration Tests (Future)
- Test full message flow with mocked Discord
- Test rate limiting across multiple users
- Test caching with concurrent requests

### Running Tests
```bash
# All tests
python -m pytest tests/

# Specific test file
python -m pytest tests/test_llm_service.py -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Monitoring & Debugging

### Key Metrics to Monitor
- Response time (p50, p95, p99)
- Cache hit rate
- API error rate
- Rate limit hit rate
- Memory usage

### Logging Best Practices
```python
logger.info("User asked question")  # Normal flow
logger.warning("Rate limit approaching")  # Warn of issues
logger.error("API request failed", exc_info=True)  # Always include exc_info
```

### Debugging Tips
1. Set `LOG_LEVEL=DEBUG` for verbose output
2. Check `bot.log` for full execution trace
3. Use `Config.to_dict()` to verify settings
4. Add temporary logs at decision points

## Security Considerations

### Secrets Management
- ✅ API keys in `.env` (not committed)
- ✅ No secrets in logs
- ✅ Env var validation on startup
- ❌ Avoid logging user prompts (may contain PII)

### Rate Limiting
- ✅ Per-user limits prevent abuse
- ✅ Per-guild limits prevent spam
- ✅ Cooldown prevents timing attacks

### Input Validation
- ✅ Prompt not empty
- ✅ Message length truncated safely
- ✅ Error messages sanitized

## Deployment Considerations

### Environment Variables
```bash
# Required
DISCORD_API_TOKEN=xxx
OPENAI_API_KEY=xxx

# Optional
LOG_LEVEL=INFO
LOG_FILE=/var/log/bot.log
```

### System Requirements
- Python 3.10+
- 100MB disk space (for dependencies + logs)
- 200MB RAM (idle)
- Internet connection

### High Availability Setup
1. Run multiple bot instances (different tokens)
2. Load balance Discord API calls
3. Use shared cache (Redis) for consistency
4. Implement graceful shutdown (SIGTERM handler)

## Future Enhancements

### Short Term
- Add database for conversation history
- Implement Redis cache for multi-instance deployments
- Add Prometheus metrics
- Add health check endpoint

### Medium Term
- Slash commands support
- Interactive buttons/modals
- User preference storage
- Conversation context per user

### Long Term
- Web dashboard for analytics
- Admin commands
- Role-based access control
- Multiple LLM models support
