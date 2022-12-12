import openai
import numpy as np
import math
from PIL import Image
import requests
from io import BytesIO
import cv2
import numpy as np
import sys
import random
import argparse
from argparse import RawTextHelpFormatter
import time
import keyboard

target_height = 512
target_width = math.ceil(target_height*1.67)

def crop(in_fn, out_fn, new_width):
    im = Image.open(in_fn + ".png")
    remove = int(math.ceil((im.width-new_width)/2)) * 2
    size = im.width - remove
    im_left = im.crop((0, 0, (im.width-size), im.height))
    im_right = im.crop((size, 0, im.width, im.height))
    im_left.save(out_fn + "_left.png")
    im_right.save(out_fn + "_right.png")

def resize(in_fn, out_fn, new_size, rs_type=None):
    """rs_type: Image.Resampling.NEAREST is no antialiasing fastest but noisy results,
                Image.Resampling.BOX is good for a little smoothing and only slightly slower,
                Image.Dither.FLOYDSTEINBERG is even more smoothing and a little slower still
    """
    if not rs_type:
        rs_type = Image.Resampling.BOX
    im = Image.open(in_fn)
    im = im.resize((new_size,new_size), rs_type)
    im.save(out_fn)

def extend(in_fn, out_fn, new_size):
    im_left = Image.open(in_fn + "_left.png")
    im_left = im_left.convert('RGBA')
    left_width, left_height = im_left.size
    x1 = (new_size - left_width) // 2
    y1 = (new_size - left_height) // 2
    new_image = Image.new('RGBA', (new_size, new_size), (0, 0, 0, 0))
    new_image.paste(im_left, (new_size-left_width, y1, new_size, y1 + left_height))
    new_image.save(out_fn + "_left.png")

    im_right = Image.open(in_fn + "_right.png")
    im_right = im_right.convert('RGBA')
    right_width, right_height = im_right.size
    x1 = (new_size - right_width) // 2
    y1 = (new_size - right_height) // 2
    new_image = Image.new('RGBA', (new_size, new_size), (0, 0, 0, 0))
    new_image.paste(im_right, (0, y1, right_width, y1 + right_height))
    new_image.save(out_fn + "_right.png")
   

def combine(in_fn, out_fn):
    im_left = Image.open(in_fn + "_left.png")
    im_right = Image.open(in_fn + "_right.png")
    im_middle = Image.open(in_fn + ".png")

    new_image = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
    new_image.paste(im_middle, ((int)((target_width/2)-(im_middle.width/2)), 0, (int)((target_width/2)+(im_middle.width/2)), target_height))
    new_image.paste(im_left, (0, 0, im_left.width, target_height))
    new_image.paste(im_right, (target_width-im_right.width, 0, target_width, target_height))
    new_image.save(out_fn + ".png")

def generate_extended_image(in_fn, out_fn, text_prompt):
    edited_image = openai.Image.create_edit(
        image=open(in_fn + "_left.png", "rb"),
        mask=open(in_fn + "_left.png", "rb"),
        prompt=text_prompt,
        n=1,
        size="512x512"
    )
    image_url = edited_image['data'][0]['url']
    #print(image_url)
    img = Image.open(BytesIO(requests.get(image_url).content))
    img.putalpha(255)
    img.save(out_fn + "_left.png")

    edited_image = openai.Image.create_edit(
        image=open(in_fn + "_right.png", "rb"),
        mask=open(in_fn + "_right.png", "rb"),
        prompt=text_prompt,
        n=1,
        size="512x512"
    )
    image_url = edited_image['data'][0]['url']
    #print(image_url)
    img = Image.open(BytesIO(requests.get(image_url).content))
    img.putalpha(255)
    img.save(out_fn + "_right.png")

def draw_gradient_alpha_rectangle(frame, BGR_Channel, rectangle_position, rotate):
    (xMin, yMin), (xMax, yMax) = rectangle_position
    color = np.array(BGR_Channel, np.uint8)[np.newaxis, :]
    mask1 = np.rot90(np.repeat(np.tile(np.linspace(1, 0, (rectangle_position[1][1]-rectangle_position[0][1])), ((rectangle_position[1][0]-rectangle_position[0][0]), 1))[:, :, np.newaxis], 3, axis=2), rotate) 
    frame[yMin:yMax, xMin:xMax, :] = mask1 * frame[yMin:yMax, xMin:xMax, :] + (1-mask1) * color

    return frame

def generate_image_from_prompt(text_prompt):
    api_key = open('api_key.txt', 'r')
    openai.api_key =  api_key.readlines()[0].strip()
    img_name = "test_image"
    response = openai.Image.create(
        prompt=text_prompt,
        n=1,
        size="512x512"
    )
    image_url = response['data'][0]['url']
    print(image_url)
    img = Image.open(BytesIO(requests.get(image_url).content))
    img.putalpha(255)
    img.save(img_name + '.png')

    crop(img_name, img_name, math.ceil((target_width-target_height)/2) )
    extend(img_name, img_name, target_height)
    generate_extended_image(img_name, img_name, text_prompt)
    combine(img_name, f"{img_name}_combined")
    return cv2.imread(f"{img_name}_combined.png", cv2.IMREAD_ANYCOLOR)

def generate_text_prompt():
    subjectprompts = open('subjectprompts.txt', 'r')
    subjects = subjectprompts.readlines()
    num_subjects = len(subjects)

    artistprompts = open('artistprompts.txt', 'r')
    artists = artistprompts.readlines()
    num_artists = len(artists)

    selected_subject = random.randint(0,num_subjects-1)
    selected_artist = random.randint(0,num_artists-1)

    return f"A painting of {subjects[selected_subject].strip()} in the style of {artists[selected_artist].strip()}"

def format_text_on_image(text_prompt, image):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.9
    font_color = (255, 255, 255)
    thickness = 1
    text_height_offset = 20
    text_width_offset = 10

    (text_width, text_height) = cv2.getTextSize(text_prompt, font, font_scale, thickness)[0]
    text_height += text_height_offset

    mask = np.zeros((text_height, text_width+text_width_offset*2), dtype=np.uint8)
    mask = cv2.putText(mask, text_prompt, (text_width_offset,text_height_offset), font, font_scale, font_color, thickness,cv2.LINE_AA)

    text_ratio = image.shape[1]/mask.shape[1]

    mask = cv2.resize(mask, (image.shape[1], int(text_height*text_ratio)))

    draw_gradient_alpha_rectangle(image, (0,0,0),((0,image.shape[0]-100),(image.shape[1],image.shape[0])),3)

    mask = cv2.merge((mask, mask, mask))
    image[-int(text_height*text_ratio):, :, :] = cv2.bitwise_or(image[-int(text_height*text_ratio):, :, :], mask)

    return image

def main():

    parser = argparse.ArgumentParser(description='Run the digital picture frame', formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i', '--interval', type=str, help='Interval that the photos should update at (in hours)', required=True)
    parser.add_argument('-c', '--use_cached', action='store_true', help='use a cached image instead of generating a new one')
    args = parser.parse_args()

    while (True):
        text_prompt = generate_text_prompt()

        if args.use_cached:
            img=cv2.imread("test_image_combined.png", cv2.IMREAD_ANYCOLOR)
        else:
            img=generate_image_from_prompt(text_prompt)

        img = format_text_on_image(text_prompt, img)
        
        cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

        cv2.imshow("window", img)
        cv2.waitKey(int(float(args.interval)*60*60*1000))
        if keyboard.is_pressed("a"):
            sys.exit() # to exit from all the processes
        
if __name__ == "__main__":
    main()


