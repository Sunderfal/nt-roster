import asyncio
import discord
import httpx
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

AWARDS_PATH = "../data/awards.json"
ENV_PATH = "../env/.env"

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

def read_json(path: str):

    with open(path, "r") as file:
        return json.load(file)
    
def update_json(path: str, data: dict):
    
    with open(path, "w") as file:
        json.dump(data, file, indent=4)
    
def find_user(data: dict, username: discord.Member):

    i = 0
    found = False
    user_found = None

    while i < len(data) and not found:
        if data[i]["username"] == username:
            found = True
            user_found = data[i]
        i += 1

    return user_found

def update_user_username(data: dict, before_username: str, after_username: str):
    
    i = 0
    found = False

    while i < len(data) and not found:
        if data[i]["username"] == before_username:
            found = True
            data[i]["username"] = after_username
        i += 1
    
    print(f"{before_username}'s username updated in the JSON to {after_username}")

def update_user_status(user: dict):

    if user["status"] == "Active":
        user["status"] = "IA"
    else:
        user["status"] = "Active"

def update_user_points(user: dict, amount: int, type: discord.app_commands.Choice[str], method: discord.app_commands.Choice[str]):

    if method == "add":
        user[type] += amount
    else:
        user[type] -= amount

        if user[type] < 0:
            user[type] = 0

def punish_user(user: dict, reason: str, evidence: str):

    today_date = str(datetime.now().date())
    is_warned = False

    strike = {"reason": reason, "date": today_date, "evidence": evidence}
    user["punishments"]["strikes"].append(strike)

    if len(user["punishments"]["strikes"]) == 3:
        is_warned = True
        
        warn = {"reason": f"Reached {len(user["punishments"]["warns"])+1}º set of Strikes", "date": today_date}
        
        user["punishments"]["warns"].append(warn)
        user["punishments"]["strikes"].clear()

    return is_warned

def get_user_avatar(interaction: discord.Interaction, member: discord.Member):

    if member is None:
        avatar = interaction.user.avatar.url if interaction.user.avatar is not None else interaction.user.default_avatar.url
    else:
        avatar = member.avatar.url if member.avatar.url is not None else member.default_avatar.url
        
    return avatar

def get_username(interaction: discord.Interaction, member: discord.Member):

    if member is None:
        username = interaction.user.display_name
    else:
        username = member.display_name

    return username

def get_id_award_by_name(award_name, award_type):

    awards = read_json(AWARDS_PATH)

    i = 0
    found = False
    id_found = None

    while i < len(awards[award_type]) and not found:
        if awards[award_type][i]["name"] == award_name:
            found = True
            id_found = awards[award_type][i]["id"]
        i += 1

    return id_found

def verify_expired_warns(user: dict):
    
    today_date = datetime.now().date()
    three_months = timedelta(days=90)

    valid_warns = []
    expired_warns = False

    for warn in user["punishments"]["warns"]:
        warn_date = datetime.strptime(warn["date"], "%Y-%m-%d").date()

        if today_date - warn_date <= three_months:
            expired_warns = True
            valid_warns.append(warn)

    user["punishments"]["warns"].clear()
    user["punishments"]["warns"].extend(valid_warns)

    return expired_warns

async def get_roblox_profile(username: str):

    url = f"https://users.roblox.com/v1/users/search?keyword={username}"
    result = None
    
    try:   
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data["data"][0]["id"]
            result = f"https://www.roblox.com/users/{user_id}/profile"
        elif response.status_code == 429:
            print("Too many requests to get the roblox profile. Trying again in 60 seconds...")
            await asyncio.sleep(60)
            result = await get_roblox_profile(username)
    except Exception as e:
        result = None
        print(f"The function 'get_roblox_profile' has throwed the following exception: {e}")

    return result

async def get_player_status(user_ids: list):
    
    url = "https://presence.roblox.com/v1/presence/users"
    roblox_security_cookie = os.getenv("ROBLOX_SECURITY_COOKIE")

    headers = {"Content-Type": "application/json", "Cookie": roblox_security_cookie, "accept": "application/json"}
    body = {"userIds": user_ids}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)
    except Exception as e:
        response = None
        print(f"The function 'get_player_status' has throwed the following exception: {e}")

    return response.json()

async def get_users_by_ids(interaction: discord.Interaction, mentions: list[str]):

    resolved_users = []

    for mention in mentions:

        if mention.startswith("<@") and mention.endswith(">"):
            user_id = mention.replace("<@", "").replace(">", "").replace("!", "")

        resolved_user = await interaction.guild.fetch_member(int(user_id))

        if resolved_user is not None:
            resolved_users.append(resolved_user)
    
    return resolved_users

async def manage_roles(member: discord.Member, user_data: dict, points: int, type: discord.app_commands.Choice[str]):
    
    awards = read_json(AWARDS_PATH)

    awards_type = "dr_roles" if type == "DR" else "pdr_roles"
    awards_points_needed = "drs_needed" if type == "DR" else "pdrs_needed"
    
    user_award_type = "dr_award" if type == "DR" else "pdr_award"
    current_user_award = user_data["current_awards"][user_award_type]  
    last_user_awards = user_data["last_awards"][user_award_type]
    new_award = None
    
    for award in awards[awards_type]:
        
        award_id = award["id"]

        award_role = member.guild.get_role(award_id)
        member_role = member.get_role(award_id)

        if member_role is None and points >= award[awards_points_needed] and award_role.name not in last_user_awards:
            new_award = award_role.name
            user_data["current_awards"][user_award_type] = new_award
            
            await member.add_roles(award_role)                
            
            if current_user_award:
                user_data["last_awards"][user_award_type].append(current_user_award)

                id = get_id_award_by_name(current_user_award, awards_type)
                role_to_remove = member.guild.get_role(id)
                
                await member.remove_roles(role_to_remove)
            
    return new_award