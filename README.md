# that tin soldier

a discord bot- I MEAN "that tin soldier" that posts random voice lines from the tf2 tin soldier at regular intervals

## features

- posts lines automatically
- configurable intervals: every minute, hour, or day
- slash commands for ez setup
- settings persist across bot restarts
- force post command for immediate line delivery

## cmds

| commands | description | permission required |
|---------|-------------|-------------------|
| `/setup #channel interval unit` | configure posting channel and frequency | Manage Server |
| `/status` | show current bot configuration | Manage Server |
| `/postnow` | force post a line immediately | Manage Server |

### setup examples
- `/setup #general 1 day` - i posts daily in #general
- `/setup #memes 30 minute` - i posts every 30 minutes
- `/setup #random 5 minute` - i posts every 5 minutes
- `/setup #general off` - disables me

## installation

1. clone this repository
2. install dependencies: `pip install -r requirements.txt`
3. create a `.env` file with your bot token
4. run the bot- "That Tin Soldier": `python bot.py`

## self-hosting

to uhhh operate that tin soldier, consider:
- usin PM2 on Windows: `pm2 start bot.py --interpreter python --name "TinSoldier"`
- hosting on a VPS or cloud service
- setting up auto-restart on system boot

## license

MIT License - See LICENSE file for details

## creditz

Tin Soldier lines from Team Fortress 2, property of Valve Corporation.
