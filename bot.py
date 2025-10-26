import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# Load token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Define file path
ITEMS_FILE = os.path.join(os.path.dirname(__file__), "items.json")

# Load existing items
if os.path.exists(ITEMS_FILE):
	with open(ITEMS_FILE, "r") as f:
		items = json.load(f)
else:
	items = []

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user}")
	try:
		await bot.tree.sync()
		print("Slash commands synced!")
	except Exception as e:
		print(e)

@bot.tree.command(name="need", description="Add an item to the list")
@app_commands.describe(item="The item you need")
async def need(interaction: discord.Interaction, item: str):
	user = interaction.user.name
	items.append({"user": user, "item": item})

	# Save to file
	with open(ITEMS_FILE, "w") as f:
		json.dump(items, f, indent=2)

	await interaction.response.send_message(f"{user} needs **{item}**!")

@bot.tree.command(name="list", description="Show all items")
async def list_items(interaction: discord.Interaction):
	if not items:
		await interaction.response.send_message("No items in the list.")
		return
	msg = "\n".join([f"{i+1}. {entry['user']} needs {entry['item']}" for i, entry in enumerate(items)])

# Start the bot
bot.run(TOKEN)