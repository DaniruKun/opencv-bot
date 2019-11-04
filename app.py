import logging
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from utils.imgproc import *

# OpenCV bot auth token
TOKEN = os.environ["TELEGRAM_TOKEN"]

commands = [
    ['GRAY', r"(?i)gr[ea]y", grey],
    ['HSV', r"(?i)hsv", hsv],
    ['RED', r"(?i)red", red],
    ['GREEN', r"(?i)green", green],
    ['BLUE', r"(?i)blue", blue],
    ['HUE', r"(?i)hue", hue],
    ['SAT', r"(?i)sat", sat],
    ['VAL', r"(?i)val", val],
    ['BLUR', r"(?i)blur", get_blur],
    ['SHARP', r"(?i)sharp", get_sharp],
    ['NORM', r"(?i)norm", norm],
    ['SOBEL', r"(?i)sobel", get_sobel],
    ['HISTEQ', r"(?i)histeq|contrast", histeq],
    ['DFT', r"(?i)fourier|dft", get_dft],
    ['ROTATE', r"(?i)rot", get_rotated],
    ['THRESH', r"(?i)^thresh", get_threshold]
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I am the OpenCV bot! Please send me something",
    )


def unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def callback_cv(update, context):
    def send_cv_frame(frame):
        cv2.imwrite("temp.png", frame)
        context.bot.send_photo(
            chat_id=update.effective_chat.id, photo=open("temp.png", "rb")
        )

    cmd = ""
    img_file = None
    img = None
    if update.effective_message.caption is not None:
        cmd = update.effective_message.caption
        img_file = context.bot.get_file(update.message.photo[-1].file_id)
    elif update.effective_message.text is not None:
        cmd = update.effective_message.text
        img_file = context.bot.get_file(
            update.message.reply_to_message.photo[-1].file_id
        )
    if img_file is not None:
        img_file.download("img.png")
        img = cv2.imread("img.png", 1)

    command_list: list = cmd.split(' ')

    func: callable = None
    arg = None

    for command in commands:
        if re.search(command[1], command_list[0]):
            func = command[2]  # assign the callable func from command dictionary

    if len(command_list) > 1:
        arg = command_list[1]
    res = None

    if arg is not None:
        res = func(img, arg)
    elif arg is None:
        res = func(img)
    send_cv_frame(res)


def main():
    updater = Updater(TOKEN, use_context=True)
    j = updater.job_queue

    dispatcher = updater.dispatcher

    # handlers
    start_handler = CommandHandler("start", start)
    unknown_handler = MessageHandler(Filters.command, unknown)
    cv_handler = MessageHandler(Filters.photo | Filters.reply, callback_cv)

    # dispatchers
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(unknown_handler)
    dispatcher.add_handler(cv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
