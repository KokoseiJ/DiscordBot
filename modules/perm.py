import os
import sqlite3
import aiosqlite
from modules.util import Bot

PERMISSION = 3

HELP = """```markdown
# Usage:
perm [get/set] [user/cmd] [list of user/commands to set permission] [0~5]

This command will manage the permission of command/user in this server. There's 7 permissions that are used by this bot:
* 0. disabled - This is only for commands.
* 1. botowner - Only the owner of the bot can recieve this permission.
* 2. svowner - Only the owner of the server can recieve this permission.
* 3. svmod
* 4. svsudoer
* 5. public - Default permission for people with no permissions
* 6. filter - This is only for the filter and can't be assigned manually.
* 9. blacklisted - This is only for users.
Only svmod or higher permissions can set the permission, and you can't change the permission if the target already has a higher permission than you or the permission you're trying to set is higher than you.
You can change the permisison of the command that has the same/lower permission, but you can't change the permission of the user who has the same permission with you.
```""" 

DBPATH = os.path.join(Bot.path, "bot_database.db")

## TODO: Move db related things to util.py

def prepare():
	with sqlite3.connect(DBPATH) as db:
		db.execute('''CREATE TABLE IF NOT EXISTS user_perm
				 	 		(user_id text, server_id text, perm_level int)''')
		db.execute('''CREATE TABLE IF NOT EXISTS cmd_perm
							(cmd text, server_id text, perm_level int)''')
		db.commit()

	return

async def main(message, **kwargs):
	cmd = message.content.split()
	if len(cmd) < 4:
		yield HELP
		return
	if cmd[1] == "get":
		if cmd[2] == "user":
			client = kwargs['client']
			info = await client.application_info()
			owner = info.owner

			userlist = [
				message.guild.get_member(int(user))
				for user in cmd[3:] if user.isnumeric()
				and message.guild.get_member(int(user))
			]
			userlist += message.mentions
			if not userlist:
				yield "No user was specified."
				return

			rtntext = ""
			async with aiosqlite.connect(DBPATH) as db:
				for user in userlist:
					if user == owner:
						rtntext += f"Permission level of {user.display_name} is 1.\n"
					elif user == message.guild.owner:
						rtntext += f"Permission level of {user.display_name} is 2.\n"
					elif user.guild_permissions.administrator:
						rtntext += f"Permission level of {user.display_name} is 3.\n"
					else:
						cursor = await db.execute(
							'''SELECT perm_level FROM user_perm
						 	  WHERE user_id=? AND server_id=?''',
							(user.id, message.guild.id)
						)
						result = await cursor.fetchone()
						perm = 5 if result is None else result[0]
						rtntext += f"Permission level of {user.display_name} is {perm}.\n"
			yield rtntext
			return

		elif cmd[2] == "cmd":
			modules = kwargs['modules']
			cmdlist = [_cmd for _cmd in cmd[3:] if _cmd in list(modules)]
			if not cmdlist:
				yield "No command was specified."
				return
			rtntext = ""
			async with aiosqlite.connect(DBPATH) as db:
				for cmd in cmdlist:
					await db.execute('''SELECT perm_level FROM cmd_perm
										WHERE cmd=? AND server_id=?''',
										(cmd, message.guild.id)
					)
					result = await db.fetchone()
					if result is None:
						perm = modules[cmd].PERMISSION
					else:
						perm = result[0]
					rtntext += f"Permission level of {cmd} is {perm}.\n"
			yield rtntext
			return

