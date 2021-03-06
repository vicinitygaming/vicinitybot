# Version 3.6

# Imports
import discord
from discord.ext import commands
from pymongo import MongoClient
from ruamel.yaml import YAML
import vacefron
from re import search

# MONGODB SETTINGS *YOU MUST FILL THESE OUT OTHERWISE YOU'LL RUN INTO ISSUES!* - Need Help? Join The Discord Support Server, Found at top of repo.
cluster = MongoClient("mongodb link here - dont forget to insert password and database name!! and remove the <>")
levelling = cluster["databasename here"]["collectionsname here"]

# Reads the config file, no need for changing.
yaml = YAML()
with open("Configs/config.yml", "r", encoding="utf-8") as file:
    config = yaml.load(file)

# Some config options which need to be stored here, again, no need for altering.
bot_channel = config['bot_channel']
talk_channels = config['talk_channels']
level_roles = config['level_roles']
level_roles_num = config['level_roles_num']

# Vac-API, no need for altering!
vac_api = vacefron.Client()


class levelsys(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.channel.id in config['talk_channels']:
            stats = levelling.find_one({"id": ctx.author.id})
            if not ctx.author.bot:
                if stats is None:
                    newuser = {"id": ctx.author.id, "tag": ctx.author.mention, "xp": 0, "rank": 1, "background": " ",
                               "circle": False, "xp_colour": "#ffffff"}
                    print(f"User: {ctx.author.id} has been added to the database! ")
                    levelling.insert_one(newuser)
                else:
                    if config['Prefix'] in ctx.content:
                        stats = levelling.find_one({"id": ctx.author.id})
                        xp = stats["xp"]
                        levelling.update_one({"id": ctx.author.id}, {"$set": {"xp": xp}})
                    else:
                        user = ctx.author
                        role = discord.utils.get(ctx.guild.roles, name=config['double_xp'])
                        if role in user.roles:
                            xp = stats["xp"] + config['xp_per_message'] * 2
                            levelling.update_one({"id": ctx.author.id}, {"$set": {"xp": xp}})
                        else:
                            xp = stats["xp"] + config['xp_per_message']
                            levelling.update_one({"id": ctx.author.id}, {"$set": {"xp": xp}})
                    lvl = 0
                    while True:
                        if xp < ((config['xp_per_level'] / 2 * (lvl ** 2)) + (config['xp_per_level'] / 2 * lvl)):
                            break
                        lvl += 1
                    xp -= ((config['xp_per_level'] / 2 * ((lvl - 1) ** 2)) + (config['xp_per_level'] / 2 * (lvl - 1)))
                    if xp == 0:
                        levelling.update_one({"id": ctx.author.id}, {"$set": {"rank": + config['xp_per_message']}})
                        embed2 = discord.Embed(title=f":tada: **LEVEL UP!**",
                                               description=f"{ctx.author.mention} just reached Level: **{lvl}**",
                                               colour=config['embed_colour'])
                        xp = stats["xp"]
                        levelling.update_one({"id": ctx.author.id},
                                             {"$set": {"rank": lvl, "xp": xp + config['xp_per_message'] * 2}})
                        print(f"User: {ctx.author} | Leveled UP To: {lvl}")
                        embed2.add_field(name="Next Level:",
                                         value=f"``{int(config['xp_per_level'] * 2 * ((1 / 2) * lvl))}xp``")
                        embed2.set_thumbnail(url=ctx.author.avatar_url)
                        await ctx.channel.send(embed=embed2)
                        for i in range(len(level_roles)):
                            if lvl == level_roles_num[i]:
                                await ctx.author.add_roles(
                                    discord.utils.get(ctx.author.guild.roles, name=level_roles[i]))
                                embed = discord.Embed(title=":tada: **ROLE UNLOCKED!**",
                                                      description=f"{ctx.author.mention} has unlocked the **{level_roles[i]}** role!",
                                                      colour=config['embed_colour'])
                                print(f"User: {ctx.author} | Unlocked Role: {level_roles[i]}")
                                embed.set_thumbnail(url=ctx.author.avatar_url)
                                await ctx.channel.send(embed=embed)

    # Rank Command
    @commands.command(aliases=config['rank_alias'])
    async def rank(self, ctx):
        member = ctx.author
        if ctx.channel.id in config['bot_channel']:
            stats = levelling.find_one({"id": ctx.author.id})
            if stats is None:
                embed = discord.Embed(description=":x: You haven't sent any messages!",
                                      colour=config['error_embed_colour'])
                await ctx.channel.send(embed=embed)
            else:
                xp = stats["xp"]
                lvl = 0
                rank = 0
                while True:
                    if xp < ((config['xp_per_level'] / 2 * (lvl ** 2)) + (config['xp_per_level'] / 2 * lvl)):
                        break
                    lvl += 1
                xp -= ((config['xp_per_level'] / 2 * (lvl - 1) ** 2) + (config['xp_per_level'] / 2 * (lvl - 1)))
                boxes = int((xp / (config['xp_per_level'] * 2 * ((1 / 2) * lvl))) * 20)
                rankings = levelling.find().sort("xp", -1)
                for x in rankings:
                    rank += 1
                    if stats["id"] == x["id"]:
                        break
                if config['image_mode'] is False:
                    embed = discord.Embed(title="{}'s Stats Menu | :bar_chart: ".format(ctx.author.name),
                                          colour=config['rank_embed_colour'])
                    embed.add_field(name="Name", value=ctx.author.mention, inline=True)
                    embed.add_field(name="XP",
                                    value=f"{xp}/{int(config['xp_per_level'] * 2 * ((1 / 2) * lvl))}",
                                    inline=True)
                    embed.add_field(name="Rank", value=f"{rank}/{ctx.guild.member_count}", inline=True)
                    embed.add_field(name="Progress Bar",
                                    value=boxes * config['completed_bar'] + (20 - boxes) * config['uncompleted_bar'],
                                    inline=False)
                    embed.add_field(name=f"Level", value=f"{lvl}", inline=False)
                    embed.set_thumbnail(url=ctx.message.author.avatar_url)
                    await ctx.channel.send(embed=embed)
                elif config['image_mode'] is True:
                    background = stats["background"]
                    circle = stats["circle"]
                    xpcolour = stats["xp_colour"]
                    avatar = member.avatar_url_as(format="png")
                    avatar_size_regex = search("\?size=[0-9]{3,4}$", str(avatar))
                    avatar = str(avatar).strip(str(avatar_size_regex.group(0))) if avatar_size_regex else str(avatar)
                    gen_card = await vac_api.rank_card(
                        username=str(member),
                        avatar=avatar,
                        level=int(lvl),
                        rank=int(rank),
                        current_xp=int(xp),
                        next_level_xp=int(config['xp_per_level'] * 2 * ((1 / 2) * lvl)),
                        previous_level_xp=0,
                        xp_color=str(xpcolour),
                        custom_background=str(background),
                        is_boosting=bool(member.premium_since),
                        circle_avatar=circle
                    )
                    embed = discord.Embed(colour=config['rank_embed_colour'])
                    embed.set_image(url=gen_card.url)
                    await ctx.send(embed=embed)

    # Leaderboard Command
    @commands.command(aliases=config['leaderboard_alias'])
    async def leaderboard(self, ctx):
        if ctx.channel.id in bot_channel:
            rankings = levelling.find().sort("xp", -1)
            i = 1
            con = config['leaderboard_amount']
            embed = discord.Embed(title=f":trophy: Leaderboard | Top {con}", colour=config['leaderboard_embed_colour'])
            for x in rankings:
                try:
                    temp = ctx.guild.get_member(x["id"])
                    tempxp = x["xp"]
                    templvl = x["rank"]
                    embed.add_field(name=f"#{i}: {temp.name}",
                                    value=f"Level: ``{templvl}``\nTotal XP: ``{tempxp}``\n", inline=True)
                    embed.set_thumbnail(url=config['leaderboard_image'])
                    i += 1
                except:
                    pass
                if i == config['leaderboard_amount'] + 1:
                    break
            await ctx.channel.send(embed=embed)

    # Reset Command
    @commands.command()
    @commands.has_role(config["admin_role"])
    async def reset(self, ctx, user=None):
        if user:
            userget = user.replace('!', '')
            levelling.update_one({"tag": userget}, {"$set": {"rank": 1, "xp": config['xp_per_message']}})
            embed = discord.Embed(title=f":white_check_mark: RESET USER", description=f"Reset User: {user}",
                                  colour=config['success_embed_colour'])
            print(f"{userget} was reset!")
            await ctx.send(embed=embed)
        else:
            prefix = config['Prefix']
            embed2 = discord.Embed(title=f":x: RESET USER FAILED",
                                   description=f"Couldn't Reset! The User: ``{user}`` doesn't exist or you didn't mention a user!",
                                   colour=config['error_embed_colour'])
            embed2.add_field(name="Example:", value=f"``{prefix}reset`` {ctx.message.author.mention}")
            print("Resetting Failed. A user was either not declared or doesn't exist!")
            await ctx.send(embed=embed2)

    # Help Command
    @commands.command(aliase="h")
    async def help(self, ctx):
        if config['help_command'] is True:
            prefix = config['Prefix']
            top = config['leaderboard_amount']
            xp = config['xp_per_message']

            embed = discord.Embed(title="**HELP PAGE | :book:**",
                                  description=f"Commands & Information. **Prefix**: ``{prefix}``",
                                  colour=config["embed_colour"])
            embed.add_field(name="Leaderboard:", value=f"``{prefix}Leaderboard`` *Shows the Top: **{top}** Users*")
            embed.add_field(name="Rank:", value=f"``{prefix}Rank`` *Shows the Stats Menu for the User*")
            embed.add_field(name="Reset:",
                            value=f"``{prefix}Reset <user>`` *Sets the user back to: ``{config['xp_per_message']}xp`` & Level: ``1``*")
            embed.add_field(name="Background:",
                            value=f"``{prefix}background <link>`` *Changes the background of your rank card if ``image_mode`` is enabled*")
            embed.add_field(name="Circlepic:",
                            value=f"``{prefix}Circlepic <True|False>`` *Changes a users image to a circle if ``image_mode`` is enabled*")
            embed.add_field(name="Update:",
                            value=f"``{prefix}Update <user>`` *Updates any missing database fields for a user when updating to a newer version*")
            embed.add_field(name="XP Colour:",
                            value=f"``{prefix}xpcolour <hex code>`` *Changes the colour of the xp bar if ``image_mode`` is enabled*")
            embed.set_footer(text=f"You will earn {xp}xp per message | XP Per Level Is: {config['xp_per_level']}xp*")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/812895798496591882/825363205853151252/ML_1.png")
            await ctx.channel.send(embed=embed)

    @commands.command()
    @commands.has_role(config["admin_role"])
    async def restart(self, ctx):
        await ctx.message.delete()
        exit("Restarting..")

    @commands.command()
    async def background(self, ctx, link):
        await ctx.message.delete()
        levelling.update_one({"id": ctx.author.id}, {"$set": {"background": f"{link}"}})
        embed = discord.Embed(title=":white_check_mark: **BACKGROUND CHANGED!**",
                              description="Your profile background has been set successfully! If your background does not update, please try a new image.")
        embed.set_thumbnail(url=link)
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def circlepic(self, ctx, value):
        await ctx.message.delete()
        if value == "True":
            levelling.update_one({"id": ctx.author.id}, {"$set": {"circle": True}})
            embed1 = discord.Embed(title=":white_check_mark: **PROFILE CHANGED!**",
                                   description="Circle Profile Picture set to: ``True``. Set to ``False`` to return to default.")
            await ctx.channel.send(embed=embed1)
        elif value == "False":
            levelling.update_one({"id": ctx.author.id}, {"$set": {"circle": False}})
            embed2 = discord.Embed(title=":white_check_mark: **PROFILE CHANGED!**",
                                   description="Circle Profile Picture set to: ``False``. Set to ``True`` to change it to a circle.")
            await ctx.channel.send(embed=embed2)
        elif value is None:
            embed3 = discord.Embed(title=":x: **SOMETHING WENT WRONG!**",
                                   description="Please make sure you either typed: ``True`` or ``False``.")
            await ctx.channel.send(embed=embed3)

    @commands.command()
    async def xpcolour(self, ctx, colour):
        await ctx.message.delete()
        if colour is None:
            embed = discord.Embed(title=":x: **SOMETHING WENT WRONG!**",
                                  description="Please make sure you typed a hex code in!.")
            await ctx.channel.send(embed=embed)
            return
        levelling.update_one({"id": ctx.author.id}, {"$set": {"xp_colour": f"{colour}"}})
        prefix = config['Prefix']
        embed = discord.Embed(title=":white_check_mark: **XP COLOUR CHANGED!**",
                              description=f"Your xp colour has been changed. If you type ``{prefix}rank`` and nothing appears, try a new hex code. \n**Example**:\n*#0000FF* = *Blue*")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/812895798496591882/825363205853151252/ML_1.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_role(config["admin_role"])
    async def update(self, ctx, user=None):
        if user:
            levelling.update_one({"id": ctx.author.id}, {"$set": {"background": "", "circle": False, "xp_colour": "#ffffff"}})
            embed = discord.Embed(title=f":white_check_mark: UPDATED USER", description=f"Updated User: {user}",
                                  colour=config['success_embed_colour'])
            await ctx.send(embed=embed)
        else:
            prefix = config['Prefix']
            embed2 = discord.Embed(title=f":x: UPDATE USER FAILED",
                                   description=f"Couldn't Update User: ``{user}`` doesn't exist or you didn't mention a user!",
                                   colour=config['error_embed_colour'])
            embed2.add_field(name="Example:", value=f"``{prefix}update`` {ctx.message.author.mention}")
            await ctx.send(embed=embed2)


def setup(client):
    client.add_cog(levelsys(client))

# End Of Level System
1
