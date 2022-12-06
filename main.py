import openai
import numpy as np
import math
from PIL import Image
import requests
from io import BytesIO
import cv2
import numpy as np
import sys

target_height = 512
target_width = math.ceil(target_height*1.67)
art_prompt = "A sculpture of a roman soldier"

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

def generate_image(out_fn):
    response = openai.Image.create(
    prompt=art_prompt,
    n=1,
    size="512x512"
    )
    image_url = response['data'][0]['url']
    print(image_url)
    img = Image.open(BytesIO(requests.get(image_url).content))
    img.putalpha(255)
    img.save(out_fn+ '.png')

def combine(in_fn, out_fn):
    im_left = Image.open(in_fn + "_left.png")
    im_right = Image.open(in_fn + "_right.png")
    im_middle = Image.open(in_fn + ".png")

    new_image = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
    new_image.paste(im_middle, ((int)((target_width/2)-(im_middle.width/2)), 0, (int)((target_width/2)+(im_middle.width/2)), target_height))
    new_image.paste(im_left, (0, 0, im_left.width, target_height))
    new_image.paste(im_right, (target_width-im_right.width, 0, target_width, target_height))
    new_image.save(out_fn + ".png")

def generate_extended_image(in_fn, out_fn):
    edited_image = openai.Image.create_edit(
        image=open(in_fn + "_left.png", "rb"),
        mask=open(in_fn + "_left.png", "rb"),
        prompt=art_prompt,
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
        prompt=art_prompt,
        n=1,
        size="512x512"
    )
    image_url = edited_image['data'][0]['url']
    #print(image_url)
    img = Image.open(BytesIO(requests.get(image_url).content))
    img.putalpha(255)
    img.save(out_fn + "_right.png")

#openai.api_key = "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"
#generate_image('test_image')
#crop('test_image', 'test_image', math.ceil((target_width-target_height)/2) )
#extend('test_image', 'test_image', target_height )
#generate_extended_image('test_image', 'test_image')
#combine("test_image", "test_image_combined")

def draw_gradient_alpha_rectangle(frame, BGR_Channel, rectangle_position, rotate):
    (xMin, yMin), (xMax, yMax) = rectangle_position
    color = np.array(BGR_Channel, np.uint8)[np.newaxis, :]
    mask1 = np.rot90(np.repeat(np.tile(np.linspace(1, 0, (rectangle_position[1][1]-rectangle_position[0][1])), ((rectangle_position[1][0]-rectangle_position[0][0]), 1))[:, :, np.newaxis], 3, axis=2), rotate) 
    frame[yMin:yMax, xMin:xMax, :] = mask1 * frame[yMin:yMax, xMin:xMax, :] + (1-mask1) * color

    return frame

img=cv2.imread("test_image_combined.png", cv2.IMREAD_ANYCOLOR)
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1.5
thickness = 2
text="A sculpture of a roman soldier"
textsize = cv2.getTextSize(text, font, font_scale, thickness)[0]
# get coords based on boundary
textX = int((img.shape[1] - textsize[0]) / 2)
textY = int(img.shape[0]-30)

rectangle = draw_gradient_alpha_rectangle(img, (0,0,0),((0,img.shape[0]-100),(img.shape[1],img.shape[0])),3)

cv2.putText(img,text,(textX, textY), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)


while True:
    cv2.imshow("window", img)
    
    cv2.waitKey(0)
    sys.exit() # to exit from all the processes
