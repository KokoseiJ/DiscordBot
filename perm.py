from bot_func import Bot

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

NUMBTOPERM = ['0(disabled)', '1(botowner)', '2(svowner)', '3(svmod)', '4(svsudoer)', '5(public)', '6(filter)', '7_RESERVED', '8_RESERVED', '9(blacklisted)']

async def perm_cmd(cmd, message, sv_perm, modules, commands):
    """
    Get user list/command list from the message, change its permission.
    """
    if len(cmd) < 3:
        pass
    elif cmd[1] == "set":
        perm = await Bot.get_user_perm(message.author, message.guild, sv_perm)
        if not perm <= 3:
            raise PermissionError("You don't have permission to use this command.")
        if cmd[2] == "user":
            # This will check if user's permission is higher than the one he
            # gave.
            if perm >= int(cmd[-1]): 
                raise PermissionError("You can't set permission higher than yours.")
            # Permission 6/0 is not for users, so They should be filtered
            elif cmd[-1] in ['6', '0']:
                raise PermissionError(f"Permission {cmd[-1]} is not for users.")
            # Resolve user's account by using guild.get_member method, getting
            # mentioned users, add them to sv_perm thing and dump it.
            userlist = [
                message.guild.get_member(int(userid))
                for userid in cmd[3:-1]
                if not (userid.startswith("<@!") or 
                message.guild.get_member(int(userid)) == None)
            ] + message.mentions
            # This will filter users who is having a higher/same permission than
            # the executor of this command.
            userlist = [
                user for user in userlist
                if perm < await Bot.get_user_perm(user, message.guild, sv_perm)
            ]
            if not userlist:
                raise ValueError("No user was specified. or Users are having a higher permission than yours.")
            usernamelist = []
            # It will cause error if the dict wasn't defined before
            try:
                sv_perm['user'][str(message.guild.id)]
            except:
                try:
                    sv_perm['user'][str(message.guild.id)] = {}
                except:
                    sv_perm['user'] = {}
                    sv_perm['user'][str(message.guild.id)] = {}

            # and set them, also processing their name
            for user in userlist:
                sv_perm['user'][str(message.guild.id)][str(user.id)] = int(cmd[-1])
                # This will append 'username#tag' format thing to usernamelist
                # if the user was not using a nickname, format will be changed
                # to nickname(username#tag) If the user is using a nickname.
                if user.name == user.display_name:
                    usernamelist.append(str(user))
                else:
                    usernamelist.append(f"{user.display_name}({str(user)})")
            # Dump the json
            await Bot.json_dump(sv_perm, 'bot_perm')
            return f"Successfully set the permission of {', '.join(usernamelist)} to {cmd[-1]}.", sv_perm

        elif cmd[2] == "cmd":
            # This will check if user has a proper permission to set the
            # permission.
            if perm > int(cmd[-1]) and not cmd[-1] == '0': 
                raise PermissionError("You can't set permission that is higher than yours.")
            # Permission 6/9 is not for commands, so They should be filtered
            elif cmd[-1] in ['6', '9']:
                raise PermissionError(f"Permission {cmd[-1]} is not for commands.")
            cmdlist = [cmdname for cmdname in cmd[3:-1] if cmdname in commands]
            # This will filter the commands that has higher permission compared
            # to executor or just disabled
            cmdlist = [cmdname for cmdname in cmdlist
                if perm <= await Bot.get_module_perm(
                    modules[cmdname], message.guild, sv_perm) or
                    await Bot.get_module_perm(
                        modules[cmdname], message.guild, sv_perm) == 0
                ]
            if not cmdlist:
                raise ValueError("No command was specified, or commands are having a higher permission than yours.")
            # It will cause error if the dict wasn't defined before
            try:
                sv_perm['command'][str(message.guild.id)]
            except:
                try:
                    sv_perm['command'][str(message.guild.id)] = {}
                except:
                    sv_perm['command'] = {}
                    sv_perm['command'][str(message.guild.id)] = {}
            # And set them.
            for cmdname in cmdlist:
                sv_perm['command'][str(message.guild.id)][cmdname] = int(cmd[-1])
            # Dump the json
            await Bot.json_dump(sv_perm, 'bot_perm')
            return f"Successfully set the permission of {', '.join(cmdlist)} to {cmd[-1]}.", sv_perm
    elif cmd[1] == "get":
        if cmd[2] == "user":
            userlist = [
                message.guild.get_member(int(userid))
                for userid in cmd[3:]
                if not (userid.startswith("<@!") or 
                message.guild.get_member(int(userid)) == None)
            ] + message.mentions
            if not userlist:
                raise ValueError("No user was specified.")
            rtnlist = []
            for user in userlist:
                if user.name == user.display_name:
                    name = str(user)
                else:
                    name = f"{user.display_name}({str(user)})"
                perm = await Bot.get_user_perm(user, message.guild, sv_perm)
                rtnlist.append(f"{name}: {NUMBTOPERM[perm]}")
            return "\n\n".join(rtnlist), sv_perm
        elif cmd[2] == 'cmd':
            cmdlist = [cmdname for cmdname in cmd[3:] if cmdname in commands]
            if not cmdlist:
                raise ValueError("No command was specified.")
            rtnlist = []
            for cmdname in cmdlist:
                perm = await Bot.get_module_perm(modules[cmdname], message.guild, sv_perm)
                rtnlist.append(f"{cmdname}: {NUMBTOPERM[perm]}")
            return "\n\n".join(rtnlist), sv_perm

    elif cmd[1] == "help":
        return HELP, sv_perm
    print(cmd)
    raise SyntaxError("Usage:\n`perm [get/set] [user/cmd] [list of user/commands to set permission] [0~5]`\nCheck `perm help` for more info.")
