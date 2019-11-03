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
NORM = r"(?i)norm"
SOBEL = r"(?i)sobel"
HISTEQ = r"(?i)histeq|contrast"
DFT = r"(?i)fourier|dft"

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
            update.message.reply_to_message.photo[-1].file_id
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

    elif re.search(NORM, cmd):
        normed = cv2.normalize(bgr, None, 0, 255, cv2.NORM_MINMAX)
        send_cv_frame(normed)

    elif re.search(SOBEL, cmd):
        ddepth = cv2.CV_16S
        scale = 1
        delta = 0

        grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(grey, ddepth, 1, 0, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(grey, ddepth, 0, 1, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

        send_cv_frame(grad)

    elif re.search(HISTEQ, cmd):
        grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        eq = cv2.equalizeHist(grey)

        send_cv_frame(eq)

    elif re.search(DFT, cmd):
        I = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        if I is None:
            logging.info('Error opening image')
            return -1

        rows, cols = I.shape
        m = cv2.getOptimalDFTSize(rows)
        n = cv2.getOptimalDFTSize(cols)
        padded = cv2.copyMakeBorder(I, 0, m - rows, 0, n - cols, cv2.BORDER_CONSTANT, value=[0, 0, 0])

        planes = [np.float32(padded), np.zeros(padded.shape, np.float32)]
        complexI = cv2.merge(planes)  # Add to the expanded another plane with zeros

        cv2.dft(complexI, complexI)  # this way the result may fit in the source matrix

        cv2.split(complexI, planes)  # planes[0] = Re(DFT(I), planes[1] = Im(DFT(I))
        cv2.magnitude(planes[0], planes[1], planes[0])  # planes[0] = magnitude
        magI = planes[0]

        matOfOnes = np.ones(magI.shape, dtype=magI.dtype)
        cv2.add(matOfOnes, magI, magI)  # switch to logarithmic scale
        cv2.log(magI, magI)

        magI_rows, magI_cols = magI.shape
        # crop the spectrum, if it has an odd number of rows or columns
        magI = magI[0:(magI_rows & -2), 0:(magI_cols & -2)]
        cx = int(magI_rows / 2)
        cy = int(magI_cols / 2)
        q0 = magI[0:cx, 0:cy]  # Top-Left - Create a ROI per quadrant
        q1 = magI[cx:cx + cx, 0:cy]  # Top-Right
        q2 = magI[0:cx, cy:cy + cy]  # Bottom-Left
        q3 = magI[cx:cx + cx, cy:cy + cy]  # Bottom-Right
        tmp = np.copy(q0)  # swap quadrants (Top-Left with Bottom-Right)
        magI[0:cx, 0:cy] = q3
        magI[cx:cx + cx, cy:cy + cy] = tmp
        tmp = np.copy(q1)  # swap quadrant (Top-Right with Bottom-Left)
        magI[cx:cx + cx, 0:cy] = q2
        magI[0:cx, cy:cy + cy] = tmp
        res = 20 * np.log(magI)

        send_cv_frame(res)

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
    cv_handler = MessageHandler(Filters.photo | Filters.reply, callback_cv)

    # dispatchers
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(unknown_handler)
    dispatcher.add_handler(cv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
