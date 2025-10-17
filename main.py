import asyncio
import os
import sys

from app.bot import main
from config.config import Config, load_config

config: Config = load_config()

if sys.platform.startswith("win") or os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

asyncio.run(main())