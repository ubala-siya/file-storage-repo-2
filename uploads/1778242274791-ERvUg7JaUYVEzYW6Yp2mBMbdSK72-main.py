import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required!")

# Bot intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
intents.members = True
intents.presences = True

# Create bot instance
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None,  # Custom help command
    case_insensitive=True
)

# Event: Bot ready
@bot.event
async def on_ready():
    logger.info(f'✅ Bot logged in as {bot.user.name} ({bot.user.id})')
    logger.info(f'🌐 Connected to {len(bot.guilds)} guilds')
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers | !help"
        ),
        status=discord.Status.online
    )
    
    # Start background tasks
    status_update.start()

# Background task: Update status every 5 minutes
@tasks.loop(minutes=5)
async def status_update():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers | !help"
        ),
        status=discord.Status.online
    )

# Event: When bot joins a new guild
@bot.event
async def on_guild_join(guild):
    logger.info(f'➕ Joined guild: {guild.name} ({guild.id})')

# Event: When bot leaves a guild
@bot.event
async def on_guild_remove(guild):
    logger.info(f'➖ Left guild: {guild.name} ({guild.id})')

# Event: Handle messages (for non-command messages)
@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Process commands
    await bot.process_commands(message)

# ==================== COMMANDS ====================

# Help Command
@bot.command(name='help', aliases=['h', 'commands'])
async def help_command(ctx, command_name: str = None):
    """Show help information"""
    if command_name:
        # Show specific command help
        command = bot.get_command(command_name)
        if command:
            embed = discord.Embed(
                title=f"📖 Help: !{command.name}",
                description=command.help or "No description available",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usage",
                value=f"`!{command.name} {command.signature}`" if command.signature else f"`!{command.name}`",
                inline=False
            )
            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join([f"`!{alias}`" for alias in command.aliases]),
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Command `!{command_name}` not found!")
    else:
        # Show all commands
        embed = discord.Embed(
            title="🤖 Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Categorize commands
        categories = {
            "General": ['help', 'ping', 'info', 'serverinfo', 'userinfo'],
            "Fun": ['say', 'embed', 'poll', '8ball', 'coinflip'],
            "Utility": ['avatar', 'invite', 'uptime', 'clear']
        }
        
        for category, cmds in categories.items():
            valid_cmds = []
            for cmd_name in cmds:
                cmd = bot.get_command(cmd_name)
                if cmd:
                    valid_cmds.append(f"`!{cmd.name}`")
            if valid_cmds:
                embed.add_field(
                    name=f"📁 {category}",
                    value=" | ".join(valid_cmds),
                    inline=False
                )
        
        embed.set_footer(text=f"Use !help <command> for more details | Prefix: !")
        await ctx.send(embed=embed)

# Ping Command
@bot.command(name='ping', aliases=['latency'])
async def ping_command(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Latency:** `{latency}ms`\n**API Latency:** `{round(bot.latency * 1000)}ms`",
        color=discord.Color.green() if latency < 200 else discord.Color.orange() if latency < 500 else discord.Color.red()
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

# Info Command
@bot.command(name='info', aliases=['botinfo', 'about'])
async def info_command(ctx):
    """Show bot information"""
    embed = discord.Embed(
        title="🤖 Bot Information",
        description="A Discord bot powered by discord.py",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
    embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
    embed.add_field(name="Users", value=sum(g.member_count for g in bot.guilds), inline=True)
    embed.add_field(name="Library", value="discord.py", inline=True)
    embed.add_field(name="Python Version", value="3.10+", inline=True)
    embed.add_field(name="Created", value=bot.user.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Uptime", value=get_uptime(), inline=True)
    
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    embed.set_footer(text="Made with ❤️ using discord.py")
    
    await ctx.send(embed=embed)

# Server Info Command
@bot.command(name='serverinfo', aliases=['server', 'guildinfo'])
async def serverinfo_command(ctx):
    """Show server information"""
    guild = ctx.guild
    
    embed = discord.Embed(
        title=f"📊 {guild.name} Server Info",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=f"{len(guild.text_channels)} Text | {len(guild.voice_channels)} Voice", inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    await ctx.send(embed=embed)

# User Info Command
@bot.command(name='userinfo', aliases=['whois', 'profile'])
async def userinfo_command(ctx, member: discord.Member = None):
    """Show user information"""
    member = member or ctx.author
    
    embed = discord.Embed(
        title=f"👤 {member.name}'s Profile",
        color=member.color if member.color != discord.Color.default() else discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="Username", value=member.name, inline=True)
    embed.add_field(name="Display Name", value=member.display_name, inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M") if member.joined_at else "Unknown", inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M"), inline=True)
    embed.add_field(name="Status", value=str(member.status).title(), inline=True)
    embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
    embed.add_field(name="Bot?", value="Yes" if member.bot else "No", inline=True)
    
    roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
    if roles:
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""), inline=False)
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    
    await ctx.send(embed=embed)

# Avatar Command
@bot.command(name='avatar', aliases=['av', 'pfp'])
async def avatar_command(ctx, member: discord.Member = None):
    """Show user's avatar"""
    member = member or ctx.author
    
    embed = discord.Embed(
        title=f"🖼️ {member.name}'s Avatar",
        color=discord.Color.blue()
    )
    
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    embed.set_image(url=avatar_url)
    embed.add_field(name="Links", value=f"[PNG]({member.avatar.url if member.avatar else member.default_avatar.url}) | [WEBP]({member.avatar.url if member.avatar else member.default_avatar.url})", inline=False)
    
    await ctx.send(embed=embed)

# Say Command
@bot.command(name='say', aliases=['echo'])
async def say_command(ctx, *, message: str):
    """Make the bot say something"""
    await ctx.message.delete()
    await ctx.send(message)

# Embed Command
@bot.command(name='embed', aliases=['em'])
async def embed_command(ctx, *, message: str):
    """Create a custom embed"""
    embed = discord.Embed(
        description=message,
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

# Poll Command
@bot.command(name='poll', aliases=['vote'])
async def poll_command(ctx, *, question: str):
    """Create a poll"""
    embed = discord.Embed(
        title="📊 Poll",
        description=question,
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"Poll by {ctx.author.name}")
    
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")
    await poll_message.add_reaction("🤷")

# 8Ball Command
@bot.command(name='8ball', aliases=['magic8ball', 'ask'])
async def eightball_command(ctx, *, question: str):
    """Ask the magic 8-ball"""
    import random
    
    responses = [
        "🎱 It is certain.",
        "🎱 It is decidedly so.",
        "🎱 Without a doubt.",
        "🎱 Yes definitely.",
        "🎱 You may rely on it.",
        "🎱 As I see it, yes.",
        "🎱 Most likely.",
        "🎱 Outlook good.",
        "🎱 Yes.",
        "🎱 Signs point to yes.",
        "🎱 Reply hazy, try again.",
        "🎱 Ask again later.",
        "🎱 Better not tell you now.",
        "🎱 Cannot predict now.",
        "🎱 Concentrate and ask again.",
        "🎱 Don't count on it.",
        "🎱 My reply is no.",
        "🎱 My sources say no.",
        "🎱 Outlook not so good.",
        "🎱 Very doubtful."
    ]
    
    embed = discord.Embed(
        title="🎱 Magic 8-Ball",
        color=discord.Color.purple()
    )
    embed.add_field(name="Question", value=question, inline=False)
    embed.add_field(name="Answer", value=random.choice(responses), inline=False)
    
    await ctx.send(embed=embed)

# Coin Flip Command
@bot.command(name='coinflip', aliases=['flip', 'coin'])
async def coinflip_command(ctx):
    """Flip a coin"""
    import random
    
    result = random.choice(["Heads", "Tails"])
    emoji = "🪙" if result == "Heads" else "🪙"
    
    embed = discord.Embed(
        title=f"{emoji} Coin Flip",
        description=f"**Result:** {result}",
        color=discord.Color.gold()
    )
    
    await ctx.send(embed=embed)

# Invite Command
@bot.command(name='invite', aliases=['addbot'])
async def invite_command(ctx):
    """Get bot invite link"""
    permissions = discord.Permissions(
        send_messages=True,
        embed_links=True,
        read_messages=True,
        read_message_history=True,
        add_reactions=True,
        use_external_emojis=True,
        attach_files=True,
        manage_messages=True,
        connect=True,
        speak=True
    )
    
    invite_url = discord.utils.oauth_url(bot.user.id, permissions=permissions)
    
    embed = discord.Embed(
        title="🔗 Invite Bot",
        description=f"[Click here to invite me!]({invite_url})",
        color=discord.Color.green()
    )
    embed.add_field(name="Bot ID", value=bot.user.id, inline=False)
    
    await ctx.send(embed=embed)

# Clear Command
@bot.command(name='clear', aliases=['purge', 'clean'])
@commands.has_permissions(manage_messages=True)
async def clear_command(ctx, amount: int = 5):
    """Clear messages (requires Manage Messages permission)"""
    if amount < 1 or amount > 100:
        await ctx.send("❌ Please specify a number between 1 and 100!")
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(
        description=f"🗑️ Deleted {len(deleted) - 1} messages!",
        color=discord.Color.green()
    )
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(3)
    await msg.delete()

# Uptime Command
@bot.command(name='uptime', aliases=['up'])
async def uptime_command(ctx):
    """Show bot uptime"""
    embed = discord.Embed(
        title="⏱️ Bot Uptime",
        description=get_uptime(),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# Error Handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Argument",
            description=f"Missing required argument: `{error.param.name}`\nUse `!help {ctx.command.name}` for usage info.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Missing Permissions",
            description=f"You need `{', '.join(error.missing_permissions)}` permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    elif isinstance(error, commands.MemberNotFound):
        embed = discord.Embed(
            title="❌ User Not Found",
            description="The specified user was not found.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    else:
        logger.error(f"Command error: {error}")
        embed = discord.Embed(
            title="❌ Error",
            description="An unexpected error occurred. Please try again later.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Helper function: Get uptime
start_time = datetime.now()

def get_uptime():
    delta = datetime.now() - start_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
