# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import threading
import os
from twitch_api import twitch_router
from youtube_api import youtube_router
from audio_api import audio_router
import comtypes

@asynccontextmanager
async def lifespan(app: FastAPI):
    comtypes.CoInitialize()
    print("Starting Selenium driver at FastAPI startup...")
    from twitch_api import start_selenium_driver
    start_selenium_driver()
    comtypes.CoUninitialize()
    yield

app = FastAPI(lifespan=lifespan)

# Mount Twitch and YouTube routers
app.include_router(twitch_router)
app.include_router(youtube_router)
app.include_router(audio_router)

# Serve React static assets
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
app.mount("/vite.svg", StaticFiles(directory="frontend/dist"), name="vite-svg")

# Catch-all route for React SPA
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    # Only serve index.html for non-API, non-static, non-vite.svg routes
    if not full_path.startswith("api/") and not full_path.startswith("assets/") and full_path != "vite.svg":
        return FileResponse("frontend/dist/index.html")
    return {"detail": "Not Found"} 