import cv2
import logging
import re
import os
import numpy as np
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# OpenCV bot auth token
TOKEN = os.environ["TELEGRAM_TOKEN"]

# OpenCV Regex
# Color
GRAY = r"(?i)gr[ea]y"
HSV = r"(?i)hsv"
# Get specific channel
RED = r"(?i)red"
GREEN = r"(?i)green"
BLUE = r"(?i)blue"

HUE = r"(?i)hue"
SAT = r"(?i)sat"
VAL = r"(?i)val"

BLUR = r"(?i)blur"
SHARP = r"(?i)sharp"

ROTATE = r"(?i)rot"
ROT_CW = r"(?i)right|cw"
ROT_CCW = r"(?i)left|ccw"

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


# Opencv
def callback_cv(update, context):
    img_file = None
    hsv = None

    def send_cv_frame(frame):
        cv2.imwrite("temp.png", frame)
        context.bot.send_photo(
            chat_id=update.effective_chat.id, photo=open("temp.png", "rb")
        )

    cmd = ""
    if update.effective_message.caption is not None:
        cmd = update.effective_message.caption
        img_file = context.bot.get_file(update.message.photo[-1].file_id)
    elif update.effective_message.text is not None:
        cmd = update.effective_message.text
        img_file = context.bot.get_file(
            update.message.reply_to_message.photo[0].file_id
        )

    logging.info(f"Message: {update.message}")
    logging.info(f"Command: {cmd}")

    img_file.download("img.png")
    bgr = cv2.imread("img.png", 1)

    if len(bgr.shape) > 1:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    if re.search(GRAY, cmd):
        if len(bgr.shape) > 1:
            grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            send_cv_frame(grey)

    elif re.search(HSV, cmd):
        if hsv is not None:
            send_cv_frame(hsv)

    elif re.search(RED, cmd):
        if len(bgr.shape) > 1:
            red = bgr[:, :, 2]
            send_cv_frame(red)

    elif re.search(GREEN, cmd):
        if len(bgr.shape) > 1:
            green = bgr[:, :, 1]
            send_cv_frame(green)

    elif re.search(BLUE, cmd):
        if len(bgr.shape) > 1:
            blue = bgr[:, :, 0]
            send_cv_frame(blue)

    elif re.search(HUE, cmd) and hsv is not None:
        hue = hsv[:, :, 0]
        send_cv_frame(hue)

    elif re.search(SAT, cmd) and hsv is not None:
        sat = hsv[:, :, 1]
        send_cv_frame(sat)

    elif re.search(VAL, cmd) and hsv is not None:
        val = hsv[:, :, 2]
        send_cv_frame(val)

    elif re.search(BLUR, cmd):
        command = cmd.split(" ")
        ksize = int(command[1])
        blur = cv2.blur(bgr, (ksize, ksize))
        send_cv_frame(blur)

    elif re.search(SHARP, cmd):
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        img = bgr
        if " " in cmd:
            command = cmd.split(" ")
            i = int(command[1])
            if i > 100:
                i = 100
        else:
            i = 1
        for i in range(1, i):
            img = cv2.filter2D(img, -1, kernel)

        send_cv_frame(img)

    elif re.search(ROTATE, cmd):
        dst = None
        if not (re.search(ROT_CW, cmd) or re.search(ROT_CCW, cmd)):
            dst = cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
        elif re.search(ROT_CW, cmd):
            dst = cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
        elif re.search(ROT_CCW, cmd):
            dst = cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)

        send_cv_frame(dst)

    else:
        return


def main():
    updater = Updater(TOKEN, use_context=True)
    j = updater.job_queue

    dispatcher = updater.dispatcher

    # handlers
    start_handler = CommandHandler("start", start)
    unknown_handler = MessageHandler(Filters.command, unknown)
    image_handler = MessageHandler(Filters.photo | Filters.reply, callback_cv)

    # dispatchers
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(unknown_handler)
    dispatcher.add_handler(image_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
