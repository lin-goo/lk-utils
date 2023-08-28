from io import BytesIO

import cv2
import numpy as np
from lk_utils.log.base import error
from PIL import Image
from PIL import ImageEnhance


def img_format_covert(image, target_format="JPEG"):
    """格式转换"""
    try:
        if isinstance(image, bytes):
            image_data = BytesIO(image)
            img_obj = Image.open(image_data)
        else:
            image_data = image
            img_obj = Image.open(image_data)
            image.seek(0, 0)
        output = BytesIO()
        img_obj = img_obj.convert("RGB")
        img_obj.save(output, format=target_format)
        output.seek(0, 0)
        return output.read()
    except Exception as e:
        error("errors", f"img_format_covert fail error: {e}")
        return image


def get_photo_format(image_data):
    """获取照片格式"""
    if isinstance(image_data, bytes):
        image_data = BytesIO(image_data)

    try:
        img_obj = Image.open(image_data)
        format = img_obj.format
        image_data.seek(0, 0)
        _format = format.lower()
    except Exception:
        _format = ""
    return _format


def get_photo_size(photo_file):
    """获取照片尺寸"""
    try:
        img_obj = Image.open(photo_file)
        size = img_obj.size
    except Exception:
        size = 0, 0
    return size


def mat_to_bytes(img, ext, params=None):
    img_encode = cv2.imencode(ext, img, params)[1]
    data_encode = np.array(img_encode)
    img_bytes = data_encode.tostring()
    return img_bytes


def bytes_to_mat(stream, flags):
    img = cv2.imdecode(np.frombuffer(stream, np.uint8), flags)
    return img


def gauss_division(image):
    """高斯滤波，图像除法"""
    src1 = image.astype(np.float32)
    gauss = cv2.GaussianBlur(image, (41, 41), 0)
    gauss1 = gauss.astype(np.float32)
    dst1 = cv2.divide(src1, gauss1) * 255.0
    dst1[dst1 >= 255] = 255
    return dst1


def get_image_var(img):
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2HSV)
    return np.mean(img)


def image_enhancement(image):
    """图像增强，增强对比度和亮度"""
    # 对比度增强
    enh_con = ImageEnhance.Contrast(image)
    # contrast = 5
    image_contrasted = enh_con.enhance(5)
    # 亮度增强
    enh_bri = ImageEnhance.Brightness(image_contrasted)
    clear = get_image_var(image_contrasted)
    # print(round(clear / 2000, 1))
    brightness = max(round(clear / 2000, 1), 1)
    # print(brightness)
    image_brightened = enh_bri.enhance(brightness)
    return image_brightened


def doc_img_filter(image):
    image = gauss_division(image)
    image = image.astype(np.uint8)

    pil_image = Image.fromarray(image)
    pil_image = image_enhancement(pil_image)

    # 去色有用的备用方法
    # pil_image = pil_image.point(lambda x: 255 if x > 129 else 0)

    image = np.asarray(pil_image)

    # 去噪点
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    image[image > 127] = 255
    image[image <= 127] = 0
    return image


class ContoursException(Exception):
    def __init__(self, value):
        self.value = value


def scale_resize(img_mat, height=None, width=None):
    """等比例缩放"""
    src_photo_height = img_mat.shape[0]
    src_photo_width = img_mat.shape[1]

    if height is None:
        scale = width / src_photo_width
    elif width is None:
        scale = height / src_photo_height
    else:
        w_scale = width / src_photo_width
        h_scale = height / src_photo_height
        scale = min(w_scale, h_scale)

    img_mat = cv2.resize(
        img_mat, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA
    )
    return img_mat


def get_contours(src_img):
    """得到图片四角"""
    sh = src_img.shape[0]
    sw = src_img.shape[1]
    img = src_img

    scale_size = 1
    if sh > 1000 or sw > 1000:
        img = scale_resize(src_img, 800, 800)
        h = img.shape[0]
        scale_size = sh / h

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    invGamma = 1.0 / 0.3
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype(
        "uint8"
    )

    gray = cv2.LUT(gray, table)
    thresh1 = cv2.adaptiveThreshold(gray, 255, 1, 1, 11, 2)

    contours, hierarchy = cv2.findContours(
        thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    def biggestRectangle(contours):
        max_area = 0
        indexReturn = -1
        for index in range(len(contours)):
            i = contours[index]
            area = cv2.contourArea(i)
            if area > 100:
                if area > max_area:  # and len(approx)==4:
                    max_area = area
                    indexReturn = index

        return indexReturn

    indexReturn = biggestRectangle(contours)
    hull = cv2.convexHull(contours[indexReturn])
    rect = cv2.boundingRect(hull)
    (x, y, w, h) = rect
    x = round(scale_size * x)
    y = round(scale_size * y)
    h = round(scale_size * h)
    w = round(scale_size * w)

    if h / w > 25:
        raise ContoursException("生成图片高度异常")

    if (1 / 25) > h / w:
        raise ContoursException("生成图片宽度异常")

    poly_node_list = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
    return poly_node_list


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = np.sum(pts, axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def get_corner_node_list(poly_node_list):
    """
    多边形四个顶点的坐标排序
    """
    center_x, center_y = np.sum(poly_node_list, axis=0) / 4
    top_left = bottom_left = top_right = bottom_right = None
    for node in poly_node_list:
        x, y = node
        if x < center_x and y < center_y:
            top_left = [int(x), int(y)]
        elif x < center_x and y > center_y:
            bottom_left = [int(x), int(y)]
        elif x > center_x and y < center_y:
            top_right = [int(x), int(y)]
        elif x > center_x and y > center_y:
            bottom_right = [int(x), int(y)]

    return top_left, bottom_left, top_right, bottom_right
