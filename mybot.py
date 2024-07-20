import os
import logging
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from archive_handler_module import archive_handle
from findvideo_module import check_file
from drive_splitter_module import make_split
from send_video_module import send_video
from forward_video_downloader import download_video
from delete_module import delete_files_in_directory
from speedtest_module import run_speed_test
from pyrogram import Client, filters
from config import (
    api_id,
    api_hash,
    bot_token
)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Create an instance
app = Client("my_bot", api_id, api_hash, bot_token=bot_token)

# Create download/temp directories if they don't exist
ivr_uploader = os.path.join(os.getcwd(), "ivr_uploader")
if not os.path.exists(ivr_uploader):
    os.makedirs(ivr_uploader)

temp_dir = os.path.join(os.getcwd(), "temp")
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

DOWNLOAD_DIR = "ivr_forward_uploader"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Number of rows per page
ROWS_PER_PAGE = 4

# Track user selections, page index, and selection state
user_selections = {}
user_pages = {}
user_states = {}

#Default Auto Delete after uploading
auto_delete = False


# Function to create the inline keyboard
def create_keyboard(names, start=0):
    buttons = []
    end = min(start + ROWS_PER_PAGE, len(names))
    for i in range(start, end):
        buttons.append([InlineKeyboardButton(f"{i + 1}. {names[i]}", callback_data=f"select_{i}")])
    if start > 0:
        buttons.append([InlineKeyboardButton("Back", callback_data="back")])
    if end < len(names):
        buttons.append([InlineKeyboardButton("Next", callback_data="next")])
    buttons.append([InlineKeyboardButton("Finish", callback_data="finish")])
    return InlineKeyboardMarkup(buttons)


# Function to create the final options keyboard
def create_final_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Re-select", callback_data="reselect")],
        [InlineKeyboardButton("Upload", callback_data="upload")]
    ])


def extract_basenames(file_paths):
    basenames = [os.path.basename(file_path) for file_path in file_paths]
    return basenames


def map_basenames_to_full_paths(basenames, common_directory):
    full_paths = [os.path.join(common_directory, basename) for basename in basenames]
    return full_paths


# define a handler function for the start command
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    # send a message back to the user
    await message.reply(
        "<b>Welcome! Forward a video message, and I will download it.</b>\n\n"
        "<b>Send</b> /leech <b>to upload video file</b>\n\n"
        "<b>Send</b> /speedtest <b>to test internet speed</b>"
    )


@app.on_message(filters.video)
async def download_videofunc(client, message):
    try:
        await download_video(client, message.chat.id, message)
    except Exception as e:
        await message.reply_text(f"An error occurred when uploading video: {e}")


# Define a handler function for /speedtest command
@app.on_message(filters.command('speedtest'))
async def handle_speedtest_command(client, message):
    result_of_speedtest = await message.reply_text("Testing internet speed, Please Wait...!")
    text = await run_speed_test()
    await result_of_speedtest.edit(text)
    await asyncio.sleep(5)
    await result_of_speedtest.delete()


# Define a handler function for /clean command
@app.on_message(filters.command('clean') & filters.private)
async def handle_speedtest_command(client, message):
    cleaning_feedback = await message.reply_text("Cleaning all the usage, Please Wait...!")
    await asyncio.sleep(2)
    delete_files_in_directory("ivr_uploader")
    delete_files_in_directory("temp")
    delete_files_in_directory("ivr_forward_uploader")
    await cleaning_feedback.edit("Done cleaning the space!")
    await asyncio.sleep(1)
    await cleaning_feedback.delete()


@app.on_message(filters.command(["setrow"]) & filters.private)
async def set_row(client, message):
    global ROWS_PER_PAGE
    # Extract the command arguments
    command_parts = message.text.split()

    if len(command_parts) != 2:
        await message.reply_text("Usage: /setrow <number>")
        return

    try:
        number = int(command_parts[1])
        if 1 <= number <= 10:
            ROWS_PER_PAGE = number
            await message.reply_text(f"You've set {ROWS_PER_PAGE} Row Per Page.")
        else:
            await message.reply_text("Please choose a number between 1 and 10.")
    except ValueError:
        await message.reply_text("Invalid number. Please enter a valid integer between 1 and 10.")


@app.on_message(filters.command(["autodelete"]) & filters.private)
async def set_autodelete(client, message):
    global auto_delete
    # Extract the command arguments
    command_parts = message.text.split()

    if len(command_parts) != 2:
        await message.reply_text("Usage: /autodelete <yes or no>")
        return

    response = command_parts[1].lower()
    if response in ["yes", "y"]:
        await message.reply_text("Auto Delete after uploading is enabled now.")
        auto_delete = True
    elif response in ["no", "n"]:
        await message.reply_text("Auto Delete after uploading is disabled now.")
        auto_delete = False
    else:
        await message.reply_text("Please enter 'yes' or 'no'.")


@app.on_message(filters.command("leech"))
async def handle_link_command(client, message):
    file_path = 'ivr_uploader'
    await archive_handle(message, file_path)
    file_paths = check_file(file_path)
    file_paths = extract_basenames(file_paths)

    user_id = message.from_user.id
    if user_id not in user_selections:
        user_selections[user_id] = []
    if user_id not in user_pages:
        user_pages[user_id] = 0
    if user_id not in user_states:
        user_states[user_id] = "selecting"  # Initial state
    await message.reply("Select names:", reply_markup=create_keyboard(file_paths, start=user_pages[user_id]))


@app.on_callback_query()
async def handle_query(client, query: CallbackQuery):
    file_path = 'ivr_uploader'
    file_paths = check_file(file_path)
    if file_paths[0]:
        basename0 = os.path.dirname(file_paths[0])
    file_paths = extract_basenames(file_paths)
    data = query.data
    message = query.message
    user_id = query.from_user.id

    if user_id not in user_selections:
        user_selections[user_id] = []
    if user_id not in user_pages:
        user_pages[user_id] = 0
    if user_id not in user_states:
        user_states[user_id] = "selecting"  # Initial state

    current_page = user_pages[user_id]
    new_text = "Select names:"
    new_keyboard = create_keyboard(file_paths, start=current_page)

    if data.startswith("select_"):
        index = int(data.split("_")[1])
        if index in user_selections[user_id]:
            user_selections[user_id].remove(index)
        else:
            user_selections[user_id].append(index)
        new_keyboard = create_keyboard(file_paths, start=current_page)

    elif data == "finish":
        selected_names = [file_paths[i] for i in user_selections[user_id]]
        new_text = "You selected:\n" + "\n".join(selected_names)
        new_keyboard = create_final_keyboard()
        user_states[user_id] = "finalizing"

    elif data == "back":
        if current_page > 0:
            user_pages[user_id] -= ROWS_PER_PAGE
        new_keyboard = create_keyboard(file_paths, start=user_pages[user_id])

    elif data == "next":
        if current_page + ROWS_PER_PAGE < len(file_paths):
            user_pages[user_id] += ROWS_PER_PAGE
        new_keyboard = create_keyboard(file_paths, start=user_pages[user_id])

    elif data == "reselect":
        user_states[user_id] = "selecting"
        user_pages[user_id] = 0
        user_selections[user_id] = []
        new_text = "Re-select names:"
        new_keyboard = create_keyboard(file_paths, start=user_pages[user_id])

    elif data == "upload":
        selected_names = [file_paths[i] for i in user_selections[user_id]]
        new_text = "Your selected names have been uploaded:\n" + "\n".join(selected_names)
        new_keyboard = None
        user_states[user_id] = "selecting"  # Reset state to allow for re-selection if needed
        user_selections[user_id] = []  # Clear selections
        selected_names = map_basenames_to_full_paths(selected_names, basename0)
        for video_path in selected_names:
            if os.path.exists(video_path):
                video_size = os.path.getsize(video_path)
                if video_size > 2000 * 1024 * 1024:
                    file_pathss = await make_split(message, video_path)
                    for video_path1 in file_pathss:
                        try:
                            await send_video(client, message.chat.id, message, video_path1, auto_delete)
                        except Exception as e:
                            await message.reply_text(f"An error occurred when uploading video: {e}")
                else:
                    try:
                        await send_video(client, message.chat.id, message, video_path, auto_delete)
                    except Exception as e:
                        await message.reply_text(f"An error occurred when uploading video: {e}")
                await asyncio.sleep(2)
            else:
                await message.reply_text('Video file not found!')
        delete_files_in_directory("temp")
        await query.message.delete()

    # Edit the message only if there's a change
    if new_text != message.text or new_keyboard != message.reply_markup:
        await query.message.edit_text(new_text, reply_markup=new_keyboard)


if __name__ == "__main__":
    print("Bot")
    app.run()
