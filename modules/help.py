PERMISSION = 5
HELP = "Prints this message.\nUsage: help [permission]"

SYSTEM_HELP = """\
?prefix:
Prints the prefix for this server. This command is not affected by the server's prefix.

?reset_prefix:
Resets the prefix of this server to the default value. This command is not affected by the server's prefix and has a permission value of 3

set_prefix:
Sets the prefix of this server. This command has a permission value of 5 and cannot be changed.

perm:
Sets/checks the permission. refer to `perm help` for more info.

reload:
Reloads the modules. This command has a permission value of 1.
"""

NUMBTOPERM = ['0(disabled)', '1(botowner)', '2(svowner)', '3(svmod)', '4(svsudoer)', '5(public)', '6(filter)', '7_RESERVED', '8_RESERVED', '9(blacklisted)']

async def main(message, **kwargs):
	sv_perm = kwargs['sv_perm']
	modules = kwargs['modules']
	Bot = kwargs['bot_func']
	cmd = message.content.split()[1:]
	if len(cmd) < 1:
		yield "Usage:\n`help [permission number]` or `help system` or `help all`"
		return
	embed = await Bot.get_embed(
		"help",
		None,
		message.author
	)
	if cmd[0] == "all":
		embed.add_field(name = "System", value = SYSTEM_HELP)
		for perm in range(9):
			helplist = [
				module_name + ":\n" + modules[module_name].HELP
				for module_name in modules
				if await Bot.get_module_perm(
					modules[module_name],
					message.guild, sv_perm
				) == perm
			]
			if helplist:
				helptxt = "\n\n".join(helplist)
				embed.add_field(name = NUMBTOPERM[perm], value = helptxt)
		yield embed
	elif cmd[0] == "system":
		embed.add_field(name = "System", value = SYSTEM_HELP)
		yield embed
	else:
		try:
			perm = int(cmd[0])
		except:
			yield "Error: permission number should be a number."
		helplist = [
				module_name + ":\n" + modules[module_name].HELP
				for module_name in modules
				if await Bot.get_module_perm(
					modules[module_name],
					message.guild, sv_perm
				) == perm
			]
		if helplist:
			helptxt = "\n\n".join(helplist)
			embed.add_field(name = NUMBTOPERM[perm], value = helptxt)
			yield embed
		else:
			yield f"Cannot find any command that has a permission {cmd[0]}."