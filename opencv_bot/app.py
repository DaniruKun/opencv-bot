import os
import cv2
import logging
import re
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from opencv_bot.utils.imgproc import (hsv, grey, red, green, blue, hue, sat, val,
                                      get_blur, get_sharp, norm, get_sobel, histeq,
                                      get_dft, get_rotated, get_threshold)

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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
    filename='app.log'
)


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I am the OpenCV bot! Please send me something",
    )


def _help(update, context):
    help_msg = """
    To use the bot, either:
    - Add to a group
    - Message the bot directly at `@opencvtbot`
    *How to use:*
    Send a photo to the bot directly or in a group where the bot is present.
    There are 2 ways to call a function:
    - Add the function with arguments in photo *caption*
    - Text in *reply* to a photo
    To see list of available commands, call `/commands`
    """
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode=telegram.ParseMode.MARKDOWN,
        text=help_msg
    )


def _commands(update, context):
    with open(os.getcwd() + '/docs/commands_list', 'r') as f:
        command_list = """"""
        for line in f:
            command_list += line

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode=telegram.ParseMode.MARKDOWN,
            text=command_list
        )


def unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def callback_cv(update, context):
    def send_cv_frame(frame):
        if frame is not None:
            try:
                cv2.imwrite("temp.png", frame)  # temporarily dump the image to disk
            except:
                logging.info('Failed to dump temp frame to disk as file!')
            context.bot.send_photo(
                chat_id=update.effective_chat.id, photo=open("temp.png", "rb")
            )
            os.remove('temp.png')
        else:
            logging.info('Cannot send empty frame!')

    cmd = ""
    img_file = None
    img = None

    if update.effective_message.caption is not None:
        cmd = update.effective_message.caption
        img_file = context.bot.get_file(update.message.photo[-1].file_id)
    elif update.effective_message.text is not None:
        cmd = update.effective_message.text
        img_file = context.bot.get_file(
            update.message.reply_to_message.photo[-1].file_id)

    if img_file is not None:
        img_file.download("img.png")  # temporarily dump image to file and read as OpenCV frame
        try:
            img = cv2.imread("img.png", 1)
        except:
            img = cv2.cv2.imread("img.png", 1)

    command_list: list = cmd.split(' ')

    func: callable = None
    arg = None

    for command in commands:
        if re.search(command[1], command_list[0]):
            func = command[2]  # assign the callable func from command dictionary

    if len(command_list) > 1:
        arg = command_list[1]
    res = None

    if func is not None:

        if arg is not None and img is not None:
            res = func(img, arg)
        elif arg is None:
            res = func(img)
        send_cv_frame(res)
        logging.info("Processed image from user: %s with func: %s" % (update.effective_user, str(func.__name__)))


def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # handlers
    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", _help)
    commands_handler = CommandHandler("commands", _commands)
    unknown_handler = MessageHandler(Filters.command, unknown)
    cv_handler = MessageHandler(Filters.photo | Filters.reply | Filters.sticker, callback_cv)

    # dispatchers
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(commands_handler)
    dispatcher.add_handler(unknown_handler)
    dispatcher.add_handler(cv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
