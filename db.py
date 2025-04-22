from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

client = AsyncIOMotorClient("mongodb://localhost:27017/")
db = client.SongLibrary
collection = db["songs5"]
