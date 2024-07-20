import time
import asyncio
import os
from thumb_creator import create_thumbnail
from video_info_module import get_video_info
from pyrogram import Client, types

# Ensure the download directory exists
DOWNLOAD_DIR = "ivr_forward_uploader"


# Progress callback function
async def progress(current, total, message, start_time, video_caption):
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time / (1024 * 1024)  # Speed in MB/s
    file_size = total / (1024 * 1024)  # Total file size in MB
    progress_percentage = current * 100 / total  # Progress percentage
    await message.edit_text(
        f"<b>Downloading:</b> {video_caption}\n\n"
        f"<b>File Size: {file_size:.2f} MB</b>\n\n"
        f"<b>Progress: {progress_percentage:.2f}%</b>\n\n"
        f"<b>Speed: {speed:.2f} MB/s</b>"
    )


# Keep track of the progress while uploading
async def progressv(current, total):
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


async def download_video(client: Client, chat_id: int, message: types.Message):
    global caption, sent_message
    if message.video:
        video = message.video
        #file_id = video.file_id
        #video_filename = video.file_name or f"{file_id}.mp4"
        video_caption = message.caption or "No caption"
        download_path = os.path.join(DOWNLOAD_DIR, video_caption + ".mp4")

        sent_message = await message.reply_text(f"<b>Downloading video to {download_path}...</b>")
        start_time = time.time()

        await client.download_media(
            message=message,
            file_name=download_path,
            progress=progress,
            progress_args=(sent_message, start_time, video_caption)
        )

        await sent_message.edit_text(f"<b>Video downloaded successfully to {download_path}</b>")
        await asyncio.sleep(1)
        await sent_message.delete()

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
            if caption == "No caption.mp4":
                with open(video_path, "rb") as video_file:
                    await client.send_video(
                        chat_id,
                        video_file,
                        width=width,
                        height=height,
                        duration=duration,
                        thumb=thumb_path,
                        supports_streaming=True,
                        disable_notification=True,
                        progress=progressv
                    )
            else:
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
                        progress=progressv
                    )
            await sent_message.delete()
            await asyncio.sleep(3)
            if check_thumb and os.path.exists(thumb_path):
                os.remove(thumb_path)
            else:
                pass
            os.remove(video_path)
        else:
            await message.reply_text('<b>Failed to Extract Video INFO</b>')

