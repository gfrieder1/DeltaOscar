## PURPOSE:      Source code of DeltaOscar bot
## AUTHOR:       Gabriel Friederichs
## AUTHOR EMAIL: gfrieder101@gmail.com
## DATE:         06/25/2023

import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import datetime
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import find
import requests
import config

## Instantiate the bot
SERVER="[SERVER]"
CLIENT="[CLIENT]"
ERROR="[ERROR]"
channel_id = config.channel_ID
activity=discord.Activity(type=discord.ActivityType.watching, name="32 GB of Twitch")
bot = commands.Bot(command_prefix='d.', status=discord.Status.online, activity=activity)

## Runs when the bot loads up (worker dyno is enabled)
@bot.event
async def on_ready():
    log(SERVER,"Bot is ready.")

##########################
# Read message and react #
##########################
@bot.event
async def on_message(msg):
    ctx = await bot.get_context(msg)
    ## If the message was sent to the Photo-PR channel and it has photos/videos in the message, upload them
    if msg.channel.id == channel_id and msg.attachments:
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif')
        video_extensions = ('.mp4', '.mov', '.avi', '.mkv')
        try:
            for attachment in msg.attachments:
                if attachment.url.endswith(image_extensions + video_extensions):
                    # Modify filename to include month name
                    mydate = datetime.datetime.now()
                    attachment.filename = mydate.strftime("%B") + "_" + attachment.filename
                    ## Upload file to Google drive
                    # Save the file to a nearby directory (temporarily)
                    await save_attachment(attachment)
                    await uploadToDrive(attachment)
                    await delete_attachment(attachment)
                    log(SERVER,str(msg.author) + " uploaded " + str(attachment.filename))
            await msg.add_reaction("✅")
            log(SERVER,"Upload complete!")
        except Exception as e:
            # Log error details
            log(ERROR, "Couldn't upload " + str(attachment.filename))
            log(ERROR,e)
            await msg.add_reaction("❌")
    
    ## Otherwise, attempt to process the message as a command
    await bot.process_commands(msg)
# END on_message

## Used to save the attachment to a local location before uploading to Drive
async def save_attachment(attachment):
    url = attachment.url
    mydate = datetime.datetime.now()
    filename = attachment.filename # Concats the month with the filename

    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
            #log(SERVER,f'Saved attachment: {filename}')
# END save_attachment

## Deletes the local copy of the file after uploading to Drive
async def delete_attachment(attachment):
    file_path = attachment.filename
    
    try:
        os.remove(file_path)
        #log(SERVER,f'Successfully deleted the file: {file_path}')
    except FileNotFoundError:
        log(ERROR,f'The file does not exist: {file_path}')
    except Exception as e:
        log(ERROR,f'An error occurred while deleting the file: {e}')
# END delete_attachment

## Uploads the local copy of the attachment to Drive
async def uploadToDrive(attachment):
    # Set the saved filepath
    file_path = attachment.filename
    #log(SERVER,os.path.exists(file_path))
    # Upload the gfile after loading a gauth instance
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    gauth.SaveCredentialsFile("mycreds.txt")
    drive = GoogleDrive(gauth)
    gfile = drive.CreateFile({'parents': [{'id': 'YOUR DRIVE ID GOES HERE'}]})
    # Read file and set it as the content of this instance.
    gfile.SetContentFile(file_path)
    gfile.Upload(param={'supportsTeamDrives': True}) # Upload the file.
# END uploadToDrive

def log(tag, msg):
    print(str(datetime.datetime.now()) + " " + str(tag) + " " + str(msg)) # explicit str() casts to allow non-string parameters
# END log

## FIRE UP THE BOT
# https://c.tenor.com/uczt3KrTY5MAAAAC/engines-top-gun-maverick.gif
bot.run(config.bot_token)