import asyncio
from application_startup import Application
from config.config_loader import ConfigLoader
from core.settings import LOG_LEVEL, PORT, WORKER
import uvicorn


if __name__ == "__main__":
    Application.Instance().startup_light()
    config_loader = ConfigLoader.get_instance()

    auto_reload = False
    if config_loader.get_value(LOG_LEVEL).lower() == "debug":
        auto_reload = True

    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=int(config_loader.get_value(PORT)),
        reload=auto_reload,
        workers=int(config_loader.get_value(WORKER)),
    )
