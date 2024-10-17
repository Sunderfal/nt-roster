import discord

POINT_TYPES = [
    discord.app_commands.Choice(name="DR", value="DR"),
    discord.app_commands.Choice(name="PDR", value="PDR")
]

METHOD_TYPES = [
    discord.app_commands.Choice(name="Add", value="add"),
    discord.app_commands.Choice(name="Remove", value="remove")
]

def has_specific_role(role_name):
    async def predicate(interaction: discord.Interaction):
        
        ok = False
        role = discord.utils.get(interaction.guild.roles, name=role_name)

        if role in interaction.user.roles:
            ok = True
        else:
            await interaction.response.send_message("You don't have permissions to execute this command.", ephemeral=True)
        
        return ok
    
    return discord.app_commands.check(predicate)