import image_ops
from PIL import Image, ImageDraw
import os
import cv2

# input kwargs contains blocks of regions that we want to keep track of
# each frame is a dict that contains all the blocks
def make_frame(**kwargs):
    frame = {}
    boxes = []
    for region, blocks in kwargs.items():
        new_blocks = []
        for block in blocks:
            new_blocks.append(image_ops.Block(block.im, block.box, block.quad))
        frame[region] = new_blocks
    return frame

# make n frames
def make_frames(n, **kwargs):
    frames = []
    for i in range(n):
        new_frame = make_frame(**kwargs)
        frames.append(new_frame)
    return frames

# translates the region by displacement
# start and end are indexes of frames
# region must be in the frame dict
def translate(frames, region, displacements):
    for i in range(len(frames)):
        frame = frames[i]
        dx, dy = displacements[i]
        blocks = frame[region]
        for block in blocks:
            (tl_x, tl_y), (tr_x, tr_y), (bl_x, bl_y), (br_x, br_y) = block.quad
            block.quad = (tl_x+dx, tl_y+dy), (tr_x+dx, tr_y+dy), (bl_x+dx, bl_y+dy), (br_x+dx, br_y+dy)
    return frames

# rotates the region around center by theta degrees counterclockwise
def rotate(frames, region, center, thetas):
    for i in range(len(frames)):
        frame = frames[i]
        theta = thetas[i]
        blocks = frame[region]
        for block in blocks:
            (tl, tr, br, bl) = block.quad
            new_tl = image_ops.rotate_point(tl, center, theta)
            new_tr = image_ops.rotate_point(tr, center, theta)
            new_br = image_ops.rotate_point(br, center, theta)
            new_bl = image_ops.rotate_point(bl, center, theta)
            block.quad = (new_tl, new_tr, new_br, new_bl)
    return frames

# squetches the region by factor times, keeping stat line/point stationary
def squetch(frames, region, stat, factors, linear=True):
    for i in range(len(frames)):
        frame = frames[i]
        factor = factors[i]
        blocks = frame[region]
        for block in blocks:
            block.quad = image_ops.squetch_quad(block.quad, stat, factor)
    return frames

# make movie from frames
def make_movie(name, frames):
    os.makedirs(os.getcwd() + "\\%s" % name)
    for i in range(len(frames)):
        frame = frames[i]
        new_canvas = Image.new('RGBA', (1200, 1200), (200, 200, 200, 255))
        for region in frame:
            image_ops.merge(new_canvas, frame[region])
        new_canvas.save(os.getcwd() + "\\%s\\img%d.png" % (name, i))
    os.system("ffmpeg -r 5 -i ./%s/img%%d.png -vcodec mpeg4 -y ./%s/%s.mp4" % (name, name, name))