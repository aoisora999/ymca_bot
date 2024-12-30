import time
import asyncio
import os
from thumb_creator import create_thumbnail
from video_info_module import get_video_info
from pyrogram import Client, types

# Ensure the download directory exists
DOWNLOAD_DIR = "ivr_forward_uploader"

async def download_video(client: Client, chat_id: int, message: types.Message):
    if message.video:
        video = message.video
        video_caption = message.caption or "No caption"
        download_path = os.path.join(DOWNLOAD_DIR, video_caption)

        sent_message = await message.reply_text(f"<b>Downloading video to {download_path}...</b>")
        start_time = time.time()

        await client.download_media(
            message=message,
            file_name=download_path
        )

        await sent_message.edit_text(f"<b>Video downloaded successfully to {download_path}</b>")
        await asyncio.sleep(1)
        await sent_message.delete()
        await message.delete()

        video_path = download_path
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
            
            disclaimer = "Disclaimer: The Videos and audio contents are not owned or created by us. The original creators and studio retain all rights to the videos and audio contents. We are solely responsible for encoding the video with Myanmar subtitles."
            
            with open(video_path, "rb") as video_file:
                # Here's where you make the caption bold and add the disclaimer
                await client.send_video(
                    chat_id,
                    video_file,
                    width=width,
                    height=height,
                    duration=duration,
                    thumb=thumb_path,
                    supports_streaming=True,
                    disable_notification=True,
                    caption=f"<b>{caption if caption != 'No caption.mp4' else 'No caption'}\n\n{disclaimer}</b>"
                )
            await sent_message.delete()
            await asyncio.sleep(3)
            if check_thumb and os.path.exists(thumb_path):
                os.remove(thumb_path)
            os.remove(video_path)
        else:
            await message.reply_text('<b>Failed to Extract Video INFO</b>')
