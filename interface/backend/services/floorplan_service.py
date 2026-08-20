import os
from pathlib import Path
from dotenv import load_dotenv
from src.mcp.client.mcp_client import ChatHouseClient

# Muat .env dari root proyek
ROOT_DIR = Path(__file__).resolve().parents[3]  # naik ke root proyek
load_dotenv(ROOT_DIR / ".env")

client = ChatHouseClient(
    base_url=os.getenv("CHATHOUSE_URL"),
    endpoint=os.getenv("CHATHOUSE_ENDPOINT", "/mcp/tools/generate_floorplans")
)

def generate_floorplan_image(rooms, style="modern"):
    """Panggil server Kaggle dan kembalikan PIL Image."""
    return client.generate_floorplan(rooms, style)