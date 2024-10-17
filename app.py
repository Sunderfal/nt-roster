import asyncio
import discord
import os
import utils.functions as functions
from datetime import datetime, timezone
from dotenv import load_dotenv
from discord.ext.commands import Bot
from utils.leaderboard_view import LeaderboardView
from utils.requirements import has_specific_role, POINT_TYPES, METHOD_TYPES

ENV_PATH = "./env/.env"
DATA_PATH = "./data/data.json"
DATA_BACKUP_PATH = "./data/data_backup.json"
LEADERSHIP_PATH = "./data/leadership.json"
GAMES_INFO_PATH = "./data/games_info.json"

NT_GENERAL_CHANNEL_ID = 1250413050788450314
NT_DUTY_CHANNEL_ID = 1281808365336530994
NT_ROLE_ID = 1169985709369724928
NT_ROLE_TRIALIST_ID = 1187773872481775666

NT_LOGO = "https://drive.usercontent.google.com/download?id=1ZYXcKZGVAB39eNDTp4XbWuKdEI5RXzp2&authuser=0"

SUCCESS = ":white_check_mark:"
PREFIX = '/'

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
    
TOKEN = os.getenv("TOKEN")

current_time = datetime.now(timezone.utc).strftime("%m/%d/%Y")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():

    print(f"Bot connected as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    
    after_roles = [role.id for role in after.roles]
    before_roles = [role.id for role in before.roles]

    username = after.display_name
    
    data = functions.read_json(DATA_PATH)
    backup_data = functions.read_json(DATA_BACKUP_PATH)

    if NT_ROLE_ID in after_roles and NT_ROLE_ID not in before_roles:
        
        user_data = functions.find_user(backup_data, username)

        if user_data is not None:
            valid_user_data = user_data
            print(f"Restored {username} in the JSON")
        else:
            roblox_profile = await functions.get_roblox_profile(username)

            valid_user_data = {
                "username": username,
                "DR": 0,  
                "PDR": 0,
                "status": "Active",
                "current_awards": {
                    "dr_award": "",
                    "pdr_award": ""
                },
                "last_awards": {
                    "dr_award": [],
                    "pdr_award": []
                },
                "punishments": {
                    "strikes": [],
                    "warns": []
                },
                "roblox_profile": roblox_profile
            }
            
            print(f"Added {username} to the JSON")

        data.append(valid_user_data)
    elif before.display_name != after.display_name:
        before_username = before.display_name
        after_username = after.display_name
        functions.update_user_username(data, before_username, after_username)
    elif NT_ROLE_ID not in after_roles and NT_ROLE_ID in before_roles: 
        data = [user for user in data if user["username"] != username]
        print(f"Removed {username} from the JSON")
    
    functions.update_json(DATA_PATH, data)

@bot.tree.error
async def error(interaction: discord.Interaction, error):

    if isinstance(error, discord.app_commands.CheckFailure):
        pass
    else:
        await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)
        print(error)

@bot.tree.command(name="commands", description="Displays information on all available commands")
@has_specific_role("Night Talons")
async def commands(interaction: discord.Interaction):

    command_author = interaction.user.display_name
    command_author_pfp = interaction.user.avatar.url if interaction.user.avatar is not None else interaction.user.default_avatar.url

    embed = discord.Embed(
        title="COMMANDS LIST",
        color=discord.Color.dark_red()
    )

    embed.set_thumbnail(url=NT_LOGO)

    embed.add_field(name="/leaderboard", value="Displays the NT members' leaderboard showing all their points and if they are active at the moment.", inline=False)
    embed.add_field(name="", value="", inline=False)
    embed.add_field(name="/info", value="Displays a member's information showing their points, status, strikes and warns.", inline=False)
    embed.add_field(name="", value="", inline=False)
    embed.add_field(name="/ia (NCO COMMAND)", value="Change a member's status to active or inactive.", inline=False)
    embed.add_field(name="", value="", inline=False)
    embed.add_field(name="/update (NCO COMMAND)", value="Adds or Removes an amount of DRs or PDRs to the members introduced.", inline=False)
    embed.add_field(name="", value="", inline=False)
    embed.add_field(name="/strike (NCO COMMAND)", value="Adds a new strike or warn to the member introduced.", inline=False)

    embed.set_footer(text=f"{command_author}   •   {current_time}", icon_url=command_author_pfp)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="Displays the NT members' leaderboard")
@has_specific_role("Night Talons")
async def leaderboard(interaction: discord.Interaction):

    data = sorted(functions.read_json(DATA_PATH), key=lambda x: x["DR"], reverse=True)

    command_author = interaction.user.display_name
    command_author_pfp = interaction.user.avatar.url if interaction.user.avatar is not None else interaction.user.default_avatar.url

    view = LeaderboardView(data, current_time, command_author, command_author_pfp)

    await interaction.response.send_message(embed=view.get_embed(), view=view)

@bot.tree.command(name="info", description="Displays a member's information")
@discord.app_commands.describe(member="Member to introduce")
@has_specific_role("Night Talons")
async def info(interaction: discord.Interaction, member: discord.Member = None):
    
    username = functions.get_username(interaction, member)
    user_pfp = functions.get_user_avatar(interaction, member)
    
    data = functions.read_json(DATA_PATH)
    user_data = functions.find_user(data, username)

    if user_data is not None:
        command_author = interaction.user.display_name
        command_author_pfp = interaction.user.avatar.url if interaction.user.avatar is not None else interaction.user.default_avatar.url

        embed = discord.Embed(
            color=discord.Color.dark_red()
        )

        embed.set_author(name=f"{user_data["username"]}'s information", icon_url=user_pfp)
        
        embed.add_field(name="POINTS", value=f"Draid Points: {user_data["DR"]}\nPure Draid Points: {user_data["PDR"]}", inline=False)
        embed.add_field(name="STATUS", value=user_data["status"], inline=False)
        embed.add_field(name="STRIKES", value=len(user_data["punishments"]["strikes"]), inline=False)
        
        warns_value = ""

        if functions.verify_expired_warns(user_data):
            functions.update_json(DATA_PATH, data)

        if len(user_data["punishments"]["warns"]) >= 1:
            for i, warn in enumerate(user_data["punishments"]["warns"]):
                warns_value += f"{i+1} -> {warn["reason"]} ({warn["date"]})\n\n"
        else:
            warns_value = "No warns registered"

        embed.add_field(name="WARNS", value=warns_value, inline=False)
        
        embed.set_footer(text=f"{command_author}   •   {current_time}", icon_url=command_author_pfp)

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("The user entered does not exist in the system.", ephemeral=True)

@bot.tree.command(name="ia", description="Change a member's status to active or inactive")
@discord.app_commands.describe(member="Member to introduce")
@has_specific_role("Talons Enforcer")
@has_specific_role("Talons Overlord")
async def ia(interaction: discord.Interaction, member: discord.Member = None):
    
    username = functions.get_username(interaction, member)

    data = functions.read_json(DATA_PATH)
    user_data = functions.find_user(data, username)    

    if user_data is not None:
        command_author = interaction.user.display_name
        command_author_pfp = interaction.user.avatar.url if interaction.user.avatar is not None else interaction.user.default_avatar.url

        functions.update_user_status(user_data)
        new_user_data = user_data["status"]

        embed = discord.Embed(
            title="STATUS UPDATED",
            description=f"{username} has been marked as **{new_user_data}**",
            color=discord.Color.dark_red()
        )

        embed.set_footer(text=f"{command_author}   •   {current_time}", icon_url=command_author_pfp)

        functions.update_json(DATA_PATH, data)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("The user entered does not exist in the system.", ephemeral=True)

@bot.tree.command(name="update", description="Adds or Removes an amount of DRs or PDRs to the members introduced")
@discord.app_commands.describe(members="Mention/Ping the members to introduce", amount="Amount of points to add", type="Type of points") 
@discord.app_commands.choices(type=POINT_TYPES)
@discord.app_commands.choices(method=METHOD_TYPES)
@has_specific_role("Talons Enforcer")
@has_specific_role("Talons Overlord")
async def update(interaction: discord.Interaction, members: str, amount: int, type: discord.app_commands.Choice[str], method: discord.app_commands.Choice[str]):

    await interaction.response.defer()
        
    data = functions.read_json(DATA_PATH)
    users = await functions.get_users_by_ids(interaction, members.split())    
    not_found_users = []    
    
    channel = bot.get_channel(NT_GENERAL_CHANNEL_ID)

    for user in users:
        username = user.display_name
        user_mention = user.mention

        user_data = functions.find_user(data, username)

        if user_data is not None:
            old_points = user_data[type.value]

            command_author = interaction.user.display_name
            command_author_pfp = interaction.user.avatar.url if interaction.user.avatar is not None else interaction.user.default_avatar.url

            functions.update_user_points(user_data, amount, type.value, method.value)
            new_points = user_data[type.value]

            method_title = "ADDED" if method.value == "add" else "REMOVED"
            title = f"DREAD RAID POINTS {method_title}" if type.value == "DR" else f"PURE DREAD RAID POINTS {method_title}"

            embed = discord.Embed(
                title=title,
                color=discord.Color.green()
            )

            type_points = "Dread Raid Points" if type.value == "DR" else "Pure Dread Draid Points"
            value = f"{type_points} before -> {old_points}\n{type_points} now -> {new_points}"
            
            embed.add_field(name=username, value=value)
            embed.set_footer(text=f"{command_author}   •   {current_time}", icon_url=command_author_pfp)

            await interaction.followup.send(embed=embed)

            award = await functions.manage_roles(user, user_data, new_points, type.value)

            if award is not None:
                await channel.send(f"Congratulations {user_mention}, you have obtained the following award: **{award}**")
        else:
            not_found_users.append(user_mention)

    functions.update_json(DATA_PATH, data)
    functions.update_json(DATA_BACKUP_PATH, data)
    await interaction.followup.send(SUCCESS, ephemeral=True)
    
    if not_found_users:
        users = ", ".join(not_found_users)
        await interaction.followup.send(f"The following users entered do not exist in the system: {users}", ephemeral=True)

@bot.tree.command(name="strike", description="Adds a new strike or warn to the member introduced")
@discord.app_commands.describe(member="Member to introduce", reason="Reason for the punishment", evidence="Proof of the punishment (gyazo)") 
@has_specific_role("Talons Enforcer")
@has_specific_role("Talons Overlord")
async def strike(interaction: discord.Interaction, member: discord.Member, reason: str, evidence: str):

    username = member.display_name

    data = functions.read_json(DATA_PATH)
    user_data = functions.find_user(data, username)

    if user_data is not None:
        command_author = interaction.user.display_name
        command_author_pfp = interaction.user.avatar

        is_warned = functions.punish_user(user_data, reason, evidence)
        punish_msg = f"striked + warned **({len(user_data["punishments"]["warns"])}º set of Strikes)**" if is_warned else "striked"

        description = f"{username} has been **Striked** + **Warned**" if is_warned else f"{username} has been **Striked**"

        embed = discord.Embed(
            title="MEMBER PUNISHED",
            description=description,
            color=discord.Color.green()
        )

        embed.set_footer(text=f"{command_author}   •   {current_time}", icon_url=command_author_pfp)

        functions.update_json(DATA_PATH, data)
        functions.update_json(DATA_BACKUP_PATH, data)
        await interaction.response.send_message(embed=embed)
        
        await member.send(f"You have been {punish_msg} for not wearing the NT uniform!\n**Striked by:** {command_author}\n**Date:** {datetime.now().date()}\n**Evidence:** {evidence}\n## if you consider that there is an explicitly valid reason for the withdrawal of your strike/warn, please contact with Sunderfal.")
    else:
        await interaction.response.send_message("The user entered does not exist in the system.", ephemeral=True)

leadership = functions.read_json(LEADERSHIP_PATH)
games_info = functions.read_json(GAMES_INFO_PATH)
previous_states = {leader["id"]: None for leader in leadership}
previous_games = {leader["id"]: None for leader in leadership}

async def nt_duty():
    
    await bot.wait_until_ready()

    channel = bot.get_channel(NT_DUTY_CHANNEL_ID)

    while not bot.is_closed():

        leaders_ids = [leader["id"] for leader in leadership]
        status_data = await functions.get_player_status(leaders_ids)

        if "userPresences" in status_data:
            for leader in leadership:
                leader_id = leader["id"]
                leader_username = leader["username"]

                current_status = None
                previous_game = None

                for user_status in status_data["userPresences"]:
                    if user_status["userId"] == leader_id:
                        current_status = user_status
                        break

                if current_status:
                    current_presence_type = current_status["userPresenceType"]
                    current_game = str(current_status.get("placeId", ""))
                    
                    previous_presence_type = previous_states[leader_id]
                    previous_game = previous_games[leader_id]

                    if current_presence_type == 2 and previous_presence_type != 2 and current_game in games_info.keys():
                        embed = discord.Embed(
                            title=f"NIGHT TALONS DUTY",
                            description="AN ENTITY HAS JOINED A GAME!",
                            color=discord.Color.dark_red()
                        )

                        game_image_url = games_info[current_game]["game_image"]

                        embed.add_field(name=f"ENTITY", value=f"[{leader_username}](https://www.roblox.com/users/{leader_id}/profile)", inline=True)
                        embed.add_field(name=f"LOCATION", value=games_info[current_game]["game_name"], inline=True)

                        embed.set_image(url=game_image_url)
                        embed.set_footer(text="In shadows deep, we take our flight, With every step, we guard the Imperator's light.", icon_url=NT_LOGO)

                        nt_role = channel.guild.get_role(NT_ROLE_ID)
                        nt_trialist_role = channel.guild.get_role(NT_ROLE_TRIALIST_ID)

                        await channel.send(f"{nt_role.mention} {nt_trialist_role.mention}", embed=embed)
                    elif current_presence_type != 2 and previous_presence_type == 2 and previous_game in games_info.keys():
                        embed = discord.Embed(
                            title=f"AN ENTITY HAS LEFT THE GAME",
                            description=f"[{leader_username}](https://www.roblox.com/users/{leader_id}/profile) has left the game!",
                            color=discord.Color.dark_red()
                        )

                        embed.set_footer(text="In shadows deep, we take our flight, With every step, we guard the Imperator's light.", icon_url=NT_LOGO)

                        await channel.send(embed=embed)

                    previous_states[leader_id] = current_presence_type
                    previous_games[leader_id] = current_game
        else:
            print("\"userPresences\" key wasn't found in the API response")

        await asyncio.sleep(60)
                    
async def main():
    asyncio.create_task(nt_duty())
    await bot.start(TOKEN)

asyncio.run(main())