import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log", filemode="a", level=logging.ERROR,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)
