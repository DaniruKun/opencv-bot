import cv2
import numpy as np
import re

hsv = lambda frame: cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
grey = lambda frame: cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
red = lambda frame: frame[:, :, 2]
green = lambda frame: frame[:, :, 1]
blue = lambda frame: frame[:, :, 0]
hue = lambda frame: hsv(frame)[:, :, 0]
sat = lambda frame: hsv(frame)[:, :, 1]
val = lambda frame: hsv(frame)[:, :, 2]


def get_blur(frame, args=None):
    ksize = int(args[0]) if args is not None else 3
    return cv2.blur(frame, (ksize, ksize))


def get_sharp(frame, args=None):
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    img = frame
    i = int(args[0]) if args is not None else 1
    i = 10 if i > 100 else i
    for i in range(1, i):
        img = cv2.filter2D(img, -1, kernel)
    return img


norm = lambda frame: cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)


def get_sobel(frame):
    ddepth = cv2.CV_16S
    scale = 1
    delta = 0
    grad_x = cv2.Sobel(
        grey(frame),
        ddepth,
        1,
        0,
        ksize=3,
        scale=scale,
        delta=delta,
        borderType=cv2.BORDER_DEFAULT,
    )
    grad_y = cv2.Sobel(
        grey(frame),
        ddepth,
        0,
        1,
        ksize=3,
        scale=scale,
        delta=delta,
        borderType=cv2.BORDER_DEFAULT,
    )
    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)
    grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
    return grad


histeq = lambda frame: cv2.equalizeHist(grey(frame))


def get_dft(frame):
    I = grey(frame)

    rows, cols = I.shape
    m = cv2.getOptimalDFTSize(rows)
    n = cv2.getOptimalDFTSize(cols)
    padded = cv2.copyMakeBorder(
        I, 0, m - rows, 0, n - cols, cv2.BORDER_CONSTANT, value=[0, 0, 0]
    )
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
    magI = magI[0 : (magI_rows & -2), 0 : (magI_cols & -2)]
    cx = int(magI_rows / 2)
    cy = int(magI_cols / 2)
    q0 = magI[0:cx, 0:cy]  # Top-Left - Create a ROI per quadrant
    q1 = magI[cx : cx + cx, 0:cy]  # Top-Right
    q2 = magI[0:cx, cy : cy + cy]  # Bottom-Left
    q3 = magI[cx : cx + cx, cy : cy + cy]  # Bottom-Right
    tmp = np.copy(q0)  # swap quadrants (Top-Left with Bottom-Right)
    magI[0:cx, 0:cy] = q3
    magI[cx : cx + cx, cy : cy + cy] = tmp
    tmp = np.copy(q1)  # swap quadrant (Top-Right with Bottom-Left)
    magI[cx : cx + cx, 0:cy] = q2
    magI[0:cx, cy : cy + cy] = tmp
    res = 20 * np.log(magI)
    return res


def get_rotated(frame, args=None):
    if args is None:
        args = ["cw"]
    if re.search(r"(?i)right|cw", args[0]):
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif re.search(r"(?i)left|ccw", args[0]):
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
