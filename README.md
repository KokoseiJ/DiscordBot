# Kyoko Kirigiri bot

This repo contains the source code of Kyoko_Kirigiri#7947. Developer's Discord account is KokoseiJ#2113.

[You can invite her using this link.](https://discordapp.com/api/oauth2/authorize?client_id=687805965042712587&scope=bot&permissions=104201280/)

***WARNING: This bot is still work in progress and It might work in unexpected way.***

Super Highschool Level Discord bot at your service!

## Features
Here's some special features:
1. Command permission
 - You can set permissions per users and commands to prevent some users from using commands to troll people, or just set it to mods-exclusive. There are 7 permission levels and 4 of them can be assigned by server owner. 
2. Changeable prefix
 - If another bot in your server is already using `!` prefix, don't worry - our kind kyoko can change its prefix for you. even if you somehow mess up with prefix or forgot what the prefix was, You can use `?prefix` or `?reset_prefix` to solve the situation.
3. Multiple functions
  - Kyoko is very smart, Just like in class trial. It can search google for you, Find some images, or even stream musics in decent quality from nicovideo with playlist support! (Currently Youtube support is removed as youtube changed its way to store video URL, I will fix it again as soon as possible)

## Programmer/Host side features
If you want to fork this bot and make/host your own bot, You might want to check this part. This bot is not just user-friendly, but also programmer/host-friendly! Kyoko is written in python and It takes advantages of being written in interpreter language.
1. Commands are being loaded dynamically
 - Yup, no more messing with main bot.py - All you have to do is write your module, rename it to the command's name and put it in `modules` folder. Kyoko will load it for you and boom, You just added a new function to the bot.
2. Reload function
 - You don't have to restart the bot just to add/test a new function! all you have to do is to type `!reload` - then It will reload modules.
3. Easily configurable
 - Color of embed, default prefix to use when there's no custom prefix set for the server and more are changeable in `config.ini`! Change some values in there, and you are done.

## Contribution
Source code of Kyoko is open-sourced, and I appreciate any form of contribution. As the bot is loading a command as a module from each files, All you have to do is write a code in separate file(without messing with mian `bot.py`) and gently send a PR to me. I will review it and merge the PR ASAP.

## TODO

### Code
 * [x] add perm command which contains help, set(which contains user, module subcommands) subcommands
 * [x] add set_prefix command
 * [ ] Migrate datas to MariaDB.
 * [ ] print "Running {cmd}..." before running the command.
 * [ ] remove import_module() function and do the same thing with `__init__.py`.
 * [ ] Add an exception that will be raised by modules when It's expected
 * [ ] DEBUGGING
 * [ ] Remove unnecessary async/await keyword
 * [ ] change type detection to use `isinstance()`
 * [ ] on_ready handler:  Do something in here, like changing the activity for every single second
 
### Modules
 
 * [x] translate 음악 module to english.
 * [x] Add help module that will display the list of commands.
 * [ ] rewrite music module, as well as merging music module and nico module - no more server_client class.
 * [ ] add docstring and comments to every modules
 * [ ] Add filter module which will allow users to add their own filters.

### Documentation
 * [x] Provide a documentation about the bot itself
 * [ ] Move TODO section to github TODO list
 * [ ] Provide a documentation about each modules
 * [ ] Provide a documentation about the format of the module