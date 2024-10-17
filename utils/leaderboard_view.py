import discord

class LeaderboardView(discord.ui.View):
    def __init__(self, data, current_time, command_author_name, command_author_pfp, timeout=180):
        super().__init__(timeout=timeout)
        self.data = data
        self.current_time = current_time
        self.command_author_name = command_author_name
        self.command_author_pfp = command_author_pfp
        self.page = 0
        self.members_per_page = 10
        self.max_pages = (len(data) + self.members_per_page - 1) // self.members_per_page

    def get_embed(self):
        start = self.page * self.members_per_page
        end = start + self.members_per_page

        embed = discord.Embed(
            title="Night Talons Leaderboard",
            color=discord.Color.dark_red()
        )

        for i, user_data in enumerate(self.data[start:end], start=start):
            embed.add_field(
                name="", 
                value=f"{i+1}. [{user_data["username"]}]({user_data["roblox_profile"]})\n**Draid Points:** {user_data["DR"]}\n**Pure Draid Points:** {user_data["PDR"]}\n**Status:** {user_data["status"]}", 
                inline=False
            )

        embed.set_footer(text=f"Page {self.page+1}/{self.max_pages}\n{self.command_author_name}   •   {self.current_time}", icon_url=self.command_author_pfp)

        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.danger)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.send_message("You are already in the first page!", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.success)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_pages - 1:
            self.page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.send_message("You are already in the last page!", ephemeral=True)