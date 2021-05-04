import inspect
import re
import sys
from asyncio import create_subprocess_shell as asyncsubshell
from asyncio import subprocess as asyncsub
from os import remove
from pathlib import Path
from sys import *
from time import gmtime, sleep, strftime
from traceback import format_exc

import requests
from telethon import *
from telethon.errors.rpcerrorlist import (
    FloodWaitError,
    MessageIdInvalidError,
    MessageNotModifiedError,
)

from .. import *
from ..dB.core import *
from ..dB.database import Var
from ..functions.all import time_formatter as tf
from ..utils import *
from ._wrappers import *

# sudo
ok = udB["SUDOS"]
if ok:
    SUDO_USERS = set(int(x) for x in ok.split())
else:
    SUDO_USERS = ""

if SUDO_USERS:
    sudos = list(SUDO_USERS)
else:
    sudos = ""

on = udB["SUDO"] if udB["SUDO"] is not None else "False"

if on == "True":
    sed = [ultroid_bot.uid, *sudos]
else:
    sed = [ultroid_bot.uid]

hndlr = "\\" + HNDLR


# decorator


def ultroid_cmd(allow_sudo=on, **args):
    args["func"] = lambda e: e.via_bot_id is None
    stack = inspect.stack()
    previous_stack_frame = stack[1]
    file_test = Path(previous_stack_frame.filename)
    file_test = file_test.stem.replace(".py", "")
    pattern = args["pattern"]
    groups_only = args.get("groups_only", False)
    admins_only = args.get("admins_only", False)
    args["outgoing"] = True

    if allow_sudo == "True":
        args["from_users"] = sed
        args["incoming"] = True

    else:
        args["outgoing"] = True

    if pattern is not None:
        if pattern.startswith(r"\#"):
            args["pattern"] = re.compile(pattern)
        else:
            args["pattern"] = re.compile(hndlr + pattern)
        reg = re.compile("(.*)")
        try:
            cmd = re.search(reg, pattern)
            try:
                cmd = (
                    cmd.group(1)
                    .replace("$", "")
                    .replace("?(.*)", "")
                    .replace("(.*)", "")
                    .replace("(?: |)", "")
                    .replace("| ", "")
                    .replace("( |)", "")
                    .replace("?((.|//)*)", "")
                    .replace("?P<shortname>\\w+", "")
                )
            except BaseException:
                pass
            try:
                LIST[file_test].append(cmd)
            except BaseException:
                LIST.update({file_test: [cmd]})
        except BaseException:
            pass
    args["blacklist_chats"] = True
    black_list_chats = list(Var.BLACKLIST_CHAT)
    if len(black_list_chats) > 0:
        args["chats"] = black_list_chats

    # check if the plugin should allow edited updates
    if "allow_edited_updates" in args and args["allow_edited_updates"]:
        args["allow_edited_updates"]
        del args["allow_edited_updates"]
    if "admins_only" in args:
        del args["admins_only"]
    if "groups_only" in args:
        del args["groups_only"]
    # check if the plugin should listen for outgoing 'messages'

    def decorator(func):
        async def wrapper(ult):
            chat = await ult.get_chat()
            if ult.fwd_from:
                return
            if groups_only and ult.is_private:
                return await eod(ult, "`Use this in group/channel.`", time=3)
            if admins_only and not chat.admin_rights:
                return await eod(ult, "`I'm not an admin.`", time=3)
            try:
                await func(ult)
            except MessageIdInvalidError:
                pass
            except MessageNotModifiedError:
                pass
            except FloodWaitError as fwerr:
                await ultroid_bot.asst.send_message(
                    Var.LOG_CHANNEL,
                    f"`FloodWaitError:\n{str(fwerr)}\n\nSleeping for {tf((fwerr.seconds + 10)*1000)}`",
                )
                sleep(fwerr.seconds + 10)
                await ultroid_bot.asst.send_message(
                    Var.LOG_CHANNEL,
                    "`CɪᴘʜᴇʀX Bot is working again`",
                )
            except events.StopPropagation:
                raise events.StopPropagation
            except KeyboardInterrupt:
                pass
            except BaseException as e:
                LOGS.exception(e)
                date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

                text = "**CɪᴘʜᴇʀX ᴇxᴄlusivᴇ ʙᴏᴛ - Error Report**\n"
                ftext = "\nDisclaimer:\nThis file uploaded ONLY here, "
                ftext += "we logged only fact of error and date, "
                ftext += "we respect your privacy, "
                ftext += "you may not report this error if you've "
                ftext += "any confidential data here, no one will see your data "
                ftext += "if you choose not to do so.\n\n"
                ftext += "--------START CɪᴘʜᴇʀX ᴇxᴄlusivᴇ ʙᴏᴛ CRASH LOG--------"
                ftext += "\nDate: " + date
                ftext += "\nGroup ID: " + str(ult.chat_id)
                ftext += "\nSender ID: " + str(ult.sender_id)
                ftext += "\n\nEvent Trigger:\n"
                ftext += str(ult.text)
                ftext += "\n\nTraceback info:\n"
                ftext += str(format_exc())
                ftext += "\n\nError text:\n"
                ftext += str(sys.exc_info()[1])
                ftext += "\n\n--------END CɪᴘʜᴇʀX ᴇxᴄlusivᴇ ʙᴏᴛ CRASH LOG--------"

                file = open("cipherx.txt", "w+")
                file.write(ftext)
                file.close()
                key = requests.post(
                    "https://nekobin.com/api/documents", json={"content": ftext}
                ).json()["result"]["key"]
                url = f"https://nekobin.com/{key}"
                text += f"\nPasted [here]({url}) too."
                if Var.LOG_CHANNEL:
                    Placetosend = Var.LOG_CHANNEL
                else:
                    Placetosend = ultroid_bot.uid
                await ultroid_bot.asst.send_file(
                    Placetosend,
                    "cipherx.txt",
                    caption=text,
                )
                remove("cipherx.txt")

        ultroid_bot.add_event_handler(wrapper, events.NewMessage(**args))
        try:
            LOADED[file_test].append(wrapper)
        except Exception:
            LOADED.update({file_test: [wrapper]})
        return wrapper

    return decorator
