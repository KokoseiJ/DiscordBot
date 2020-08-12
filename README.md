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
  - Kyoko is very smart, Just like in class trial. It can search google for you, Find some images, or even stream musics in decent quality from nicovideo and youtube with playlist support!

## Programmer/Host side features
If you want to fork this bot and make/host your own bot, You might want to check this part. This bot is not just user-friendly, but also programmer/host-friendly! Kyoko is written in python and It takes advantages of being written in interpreter language.
1. Commands are being loaded dynamically
 - Yup, no more messing with main bot.py - All you have to do is write your module, rename it to the command's name and put it in `modules` folder. Kyoko will load it for you and boom, You just added a new function to the bot.
2. Reload function
 - You don't have to restart the bot just to add/test a new function! all you have to do is to type `!reload` - then It will reload modules.
3. Easily configurable
 - Color of embed, default prefix to use when there's no custom prefix set for the server and more are changeable in `config.ini`! Change some values in there, and you are done.

## I want to use some of the modules in my bot
Yes, you can do it! in fact, All you have to do is getting a module file/`bot_func.py` and import it to your bot. then you can call `module.main(message)` - returned value will be async generator. the type of returned value can be either string, discord.Embed, discord.File, or None if message needs to be deleted. I am planning to write a documentation about this, but it's not here yet - so please read the code and check if it uses any of additional parameters.

## Contribution
Source code of Kyoko is distributed under GNU Public License version 3, and I appreciate any form of contribution. As the bot is loading a command as a module from each files, All you have to do is write a code in separate file(without messing with main `bot.py`) and gently send a PR to me. I will review it and merge the PR ASAP.

## TODO
Please check [issue #2](https://github.com/KokoseiJ/DiscordBot/issues/2).
