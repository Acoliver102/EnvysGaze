import numpy as np
import cv2 as cv
import pytesseract
import pandas as pd
import re


# isolate individual names and stats from scoreboard
# assumes scoreboard is a full screencap (just use PrintScreen)
def crop_img_players(img, scale=1.0):
    center_x, center_y = img.shape[1] / 2, img.shape[0] / 2
    width_scaled, height_scaled = img.shape[1] * scale, img.shape[0] * scale
    left_x, right_x = center_x - width_scaled / 4.2, center_x - width_scaled / 24
    top_y, bottom_y = center_y - height_scaled / 2.5, center_y + height_scaled / 2.25
    img_cropped = img[int(top_y):int(bottom_y), int(left_x):int(right_x)]
    return img_cropped


def crop_img_names(img, scale, player_num):
    if player_num > 4:
        player_num += 0.5
    center_x, center_y = img.shape[1] / 2, img.shape[0] / 2
    width_scaled, height_scaled = img.shape[1] * scale, img.shape[0] * scale
    left_x, right_x = center_x - width_scaled / 4.25, center_x - width_scaled / 24
    top_y, bottom_y = center_y - height_scaled * (0.325 - 0.075 * player_num), center_y - height_scaled * (
                0.25 - 0.075 * player_num)
    img_cropped = img[int(top_y):int(bottom_y), int(left_x):int(right_x)]
    return img_cropped


def crop_img_kills(img, scale, player_num):
    if player_num > 4:
        player_num += 0.5
    center_x, center_y = img.shape[1] / 2, img.shape[0] / 2
    width_scaled, height_scaled = img.shape[1] * scale, img.shape[0] * scale
    left_x, right_x = center_x + width_scaled / 38, center_x + width_scaled * 0.105
    top_y, bottom_y = center_y - height_scaled * (0.325 - 0.075 * player_num), center_y - height_scaled * (
                0.25 - 0.075 * player_num)
    img_cropped = img[int(top_y):int(bottom_y), int(left_x):int(right_x)]
    return img_cropped


def crop_img_deaths(img, scale, player_num):
    if player_num > 4:
        player_num += 0.5
    center_x, center_y = img.shape[1] / 2, img.shape[0] / 2
    width_scaled, height_scaled = img.shape[1] * scale, img.shape[0] * scale
    left_x, right_x = center_x + width_scaled * 0.1, center_x + width_scaled * 0.2
    top_y, bottom_y = center_y - height_scaled * (0.325 - 0.075 * player_num), center_y - height_scaled * (
                0.25 - 0.075 * player_num)
    img_cropped = img[int(top_y):int(bottom_y), int(left_x):int(right_x)]
    return img_cropped


def crop_img_assists(img, scale, player_num):
    if player_num > 4:
        player_num += 0.4
    center_x, center_y = img.shape[1] / 2, img.shape[0] / 2
    width_scaled, height_scaled = img.shape[1] * scale, img.shape[0] * scale
    left_x, right_x = center_x + width_scaled * 0.175, center_x + width_scaled * 0.3
    top_y, bottom_y = center_y - height_scaled * (0.325 - 0.075 * player_num), center_y - height_scaled * (
                0.25 - 0.075 * player_num)
    img_cropped = img[int(top_y):int(bottom_y), int(left_x):int(right_x)]
    return img_cropped


# get image to be more consistent for OCR
def preprocess_img(img):
    # Change all pixels to black, if they aren't white already (since all characters were white)
    img[img <= 200] = 0
    # Scale it 10x
    scaled = cv.resize(img, (0, 0), fx=10, fy=10, interpolation=cv.INTER_AREA)
    # Retained your bilateral filter
    filtered = cv.bilateralFilter(scaled, 11, 17, 17)
    # Thresholded OTSU method
    thresh = cv.threshold(filtered, 0, 255, cv.THRESH_BINARY_INV | cv.THRESH_OTSU)[1]
    # Erode the image to bulk it up for tesseract
    kernel = np.ones((5, 5), np.uint8)
    eroded = cv.erode(thresh, kernel, iterations=1)
    return eroded


# takes in path to image, returns dataframe containing game data
def image_to_dataframe(file):
    # load in image
    img = cv.imread(file)

    # Path to OCR
    pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract'
    # create dataframe
    df = pd.DataFrame(columns=['player', 'kills', 'deaths', 'assists'])

    # iterate through names, could probably change to only threshold image once for efficiency but we not there yet
    for i in range(10):
        # get name first
        img_crop = crop_img_names(img, 0.75, i)
        img_HSV = cv.cvtColor(img_crop, cv.COLOR_BGR2HSV)

        blur = cv.blur(img_HSV, (1, 1))
        blur = cv.resize(blur, (0, 0), fx=5, fy=5, interpolation=cv.INTER_LANCZOS4)
        thresh = cv.inRange(blur, (0, 0, 200), (255, 60, 255))
        thresh_inv = cv.bitwise_not(thresh)

        kernel = np.ones((5, 5), np.uint8)
        thresh_inv_eroded = cv.erode(thresh_inv, kernel, iterations=1)

        # PSM 7 needed for OCR to work on digits
        name = pytesseract.image_to_string(thresh_inv_eroded, config='--oem 3 --psm 7').strip()

        # crop and isolate kill
        img_crop = crop_img_kills(img, 0.75, i)
        img_HSV = cv.cvtColor(img_crop, cv.COLOR_BGR2HSV)

        blur = cv.blur(img_HSV, (1, 1))
        blur = cv.resize(blur, (0, 0), fx=5, fy=5, interpolation=cv.INTER_LANCZOS4)
        thresh = cv.inRange(blur, (0, 0, 150), (255, 100, 255))
        thresh_inv = cv.bitwise_not(thresh)

        kernel = np.ones((5, 5), np.uint8)
        thresh_inv_eroded = cv.dilate(thresh_inv, kernel, iterations=1)

        # PSM 6 so OCR parses as digits
        kills = re.sub('S', '5', pytesseract.image_to_string(thresh_inv_eroded, config='--oem 3 --psm 6').strip())
        kills = re.sub('V', '1', kills)
        kills = re.sub('=', '8', kills)
        kills = re.sub(':', '9', kills)

        # bracketing loop to deal with variable scoreboards, helps reduce raw mishaps
        if not kills.isnumeric() or not kills:
            thresh_inv_eroded = thresh_inv

            kills = re.sub('S', '5', pytesseract.image_to_string(thresh_inv_eroded, config='--oem 3 --psm 6').strip())
            kills = re.sub('V', '1', kills)
            kills = re.sub('=', '8', kills)
            kills = re.sub(':', '9', kills)

        # ensure that all data ends up as numbers, so that way pandas works fine
        # also helps with empty SBs
        if not kills.isnumeric() or not kills:
            kills = 0

        # convert to integer
        kills = int(kills)

        # repeat the same process for deaths and assists
        # probably some DRY that needs to be fixed but if it works it works
        img_crop = crop_img_deaths(img, 0.75, i)
        img_HSV = cv.cvtColor(img_crop, cv.COLOR_BGR2HSV)

        blur = cv.blur(img_HSV, (1, 1))
        blur = cv.resize(blur, (0, 0), fx=5, fy=5, interpolation=cv.INTER_LANCZOS4)
        thresh = cv.inRange(blur, (0, 0, 150), (255, 100, 255))
        thresh_inv = cv.bitwise_not(thresh)

        kernel = np.ones((5, 5), np.uint8)
        thresh_inv_eroded = cv.dilate(thresh_inv, kernel, iterations=1)

        deaths = re.sub('S', '5', pytesseract.image_to_string(thresh_inv_eroded, config='--oem 3 --psm 6').strip())
        deaths = re.sub('V', '1', deaths)
        deaths = re.sub('=', '8', deaths)
        deaths = re.sub(':', '9', deaths)

        if not deaths.isnumeric() or not deaths:
            thresh_inv_eroded = thresh_inv

            deaths = re.sub('S', '5', pytesseract.image_to_string(thresh_inv_eroded, config='--oem 3 --psm 6').strip())
            deaths = re.sub('V', '1', deaths)
            deaths = re.sub('=', '8', deaths)
            deaths = re.sub(':', '9', deaths)

        if not deaths.isnumeric() or not deaths:
            deaths = 0

        deaths = int(deaths)

        img_crop = crop_img_assists(img, 0.75, i)
        img_HSV = cv.cvtColor(img_crop, cv.COLOR_BGR2HSV)

        blur = cv.blur(img_HSV, (1, 1))
        blur = cv.resize(blur, (0, 0), fx=5, fy=5, interpolation=cv.INTER_LANCZOS4)
        thresh = cv.inRange(blur, (0, 0, 150), (255, 100, 255))
        thresh_inv = cv.bitwise_not(thresh)

        kernel = np.ones((5, 5), np.uint8)
        thresh_inv_eroded = cv.dilate(thresh_inv, kernel, iterations=1)

        assists = re.sub('S', '5', pytesseract.image_to_string(thresh_inv_eroded, config='--oem 3 --psm 6').strip())
        assists = re.sub('V', '1', assists)
        assists = re.sub('=', '8', assists)
        assists = re.sub(':', '9', assists)

        if not assists.isnumeric() or not assists:
            thresh_inv_eroded = thresh_inv

            assists = re.sub('S', '5', pytesseract.image_to_string(thresh_inv_eroded, config='--oem 3 --psm 6').strip())
            assists = re.sub('V', '1', assists)
            assists = re.sub('=', '8', assists)
            assists = re.sub(':', '9', assists)

        if not assists.isnumeric() or not assists:
            assists = 0

        assists = int(assists)

        # upload the data as new row in dataframe
        df.loc[len(df.index)] = [name, kills, deaths, assists]

    # print to keep track of progress in console
    print("Finished processing " + file + ".")

    return df
