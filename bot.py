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

# Define file paths
ITEMS_FILE = os.path.join(os.path.dirname(__file__), "items.json")
CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "list_channels.json")

# Load existing items
if os.path.exists(ITEMS_FILE):
	with open(ITEMS_FILE, "r") as f:
		items = json.load(f)
else:
	items = []

# Load list channels mapping
if os.path.exists(CHANNELS_FILE):
	with open(CHANNELS_FILE, "r") as f:
		list_channels = json.load(f)
else:
	list_channels = {}

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user}")
	try:
		await bot.tree.sync()
		print("Slash commands synced!")
	except Exception as e:
		print(e)

# ------------------------
# Admin: set pinned list channel
# ------------------------
@bot.tree.command(name="setlistchannel", description="Set the channel where the pinned list will be stored")
@app_commands.describe(channel="Select the channel for the pinned list")
async def set_list_channel(interaction: discord.Interaction, channel: discord.TextChannel):
	if not interaction.user.guild_permissions.administrator:
		await interaction.response.send_message("Only admins can do this.", ephemeral=True)
		return

	guild_id = str(interaction.guild.id)
	list_channels[guild_id] = channel.id

	with open(CHANNELS_FILE, "w") as f:
		json.dump(list_channels, f, indent=2)

	await interaction.response.send_message(f"List channel set to {channel.mention}", ephemeral=True)

# ------------------------
# Function to update pinned message
# ------------------------
async def update_pinned_list(guild_id: int):
	guild_id_str = str(guild_id)
	if guild_id_str not in list_channels:
		# No channel configured
		return

	channel_id = list_channels[guild_id_str]
	channel = bot.get_channel(channel_id)
	if not channel:
		print(f"Channel {channel_id} not found for guild {guild_id}")
		return

	# Find pinned messages by this bot
	pins = await channel.pins()
	bot_pins = [m for m in pins if m.author == bot.user]

	# Build Markdown table
	msg_content = "Item | Needed by\n--- | ---\n" + "\n".join(
		f"{e['item']} | {e['user']}" for e in items if e.get("guild_id") == guild_id
	)

	if bot_pins:
		await bot_pins[0].edit(content=msg_content)
	else:
		msg = await channel.send(msg_content)
		await msg.pin()

# ------------------------
# /need command
# ------------------------
@bot.tree.command(name="need", description="Add an item to the list")
@app_commands.describe(item="The item you need")
async def need(interaction: discord.Interaction, item: str):
	user = interaction.user.name
	guild_id = interaction.guild.id

	# Save item with guild info
	items.append({"user": user, "item": item, "guild_id": guild_id})

	with open(ITEMS_FILE, "w") as f:
		json.dump(items, f, indent=2)

	await interaction.response.send_message(f"{user} needs **{item}**!", ephemeral=True)

	# Update pinned list for this server
	await update_pinned_list(guild_id)

# ------------------------
# /list command
# ------------------------
@bot.tree.command(name="list", description="Show all items in the list")
async def list_items(interaction: discord.Interaction):
	guild_id = interaction.guild.id
	guild_items = [e for e in items if e.get("guild_id") == guild_id]

	if not guild_items:
		await interaction.response.send_message("No items in the list.")
		return

	msg_content = "Item | Needed by\n--- | ---\n" + "\n".join(
		f"{e['item']} | {e['user']}" for e in guild_items
	)

	await interaction.response.send_message(msg_content)

# ------------------------
# Start the bot
# ------------------------
bot.run(TOKEN)
