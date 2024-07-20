import asyncio
import os
from thumb_creator import create_thumbnail
from video_info_module import get_video_info
from pyrogram import Client, types

# Keep track of the progress while uploading
async def progress(current, total):
    global caption
    file_size = total / (1024 * 1024)  # File size in MB
    if current % (5 * 1024 * 1024) == 0:
        print(f"{current * 100 / total:.1f}%")
        await sent_message.edit(
            f"<b>File Name:</b> {caption}</b>\n\n"
            f"<b>File Size:</b> {file_size:.2f} MB</b>\n\n"
            f"<b>Uploading Progress:</b> {current * 100 / total:.1f}%</b>\n\n"
            "<b>State: Uploading</b>"
        )
    else:
        pass

async def send_video(client: Client, chat_id: int, message: types.Message, video_path: str, autodelete: bool):
    global caption, sent_message
    caption = os.path.basename(video_path)
    dimensions = get_video_info(video_path)
    if dimensions:
        width, height, duration = dimensions
        thumb_path = None
        if duration < 60:
            check_thumb = False
        else:
            check_thumb = True
            try:
                thumb_path = create_thumbnail(video_path, duration=(duration / 4))
            except:
                pass
        sent_message = await message.reply_text('<b>Starting to Upload...</b>')
        with open(video_path, "rb") as video_file:
            await client.send_video(
                chat_id,
                video_file,
                width=width,
                height=height,
                duration=duration,
                thumb=thumb_path,
                caption=caption,
                supports_streaming=True,
                disable_notification=True,
                progress=progress
            )
        await sent_message.delete()
        await asyncio.sleep(3)
        if autodelete:
            os.remove(video_path)
        else:
            pass
        if check_thumb and os.path.exists(thumb_path):
            os.remove(thumb_path)
        else:
            pass
    else:
        await message.reply_text('<b>Failed to Extract Video INFO</b>')

