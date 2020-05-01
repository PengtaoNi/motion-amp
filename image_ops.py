from PIL import Image, ImageDraw
import numpy as np
import math

# returns whether box1 contains box2
def contains_box(box1, box2):
    l1, t1, r1, b1 = box1
    l2, t2, r2, b2 = box2
    return l1 <= l2 and t1 <= t2 and r1 >= r2 and b1 >= b2

# returns the union of all boxes
def union_boxes(boxes):
    ls, rs, ts, bs = [], [], [], []
    for box in boxes:
        ls.append(box[0])
        ts.append(box[1])
        rs.append(box[2])
        bs.append(box[3])
    return (min(ls), min(ts), max(rs), max(bs))

# # translates region in im by (dx, dy)
# def translate_region(im, box, dx, dy):
#     new_box = (box[0]+dx, box[1]+dy, box[2]+dx, box[3]+dy)
#     new_im = im.crop(box)
#     draw = ImageDraw.Draw(im)
#     draw.rectangle(box, fill=(255,255,255,0))
#     im.paste(new_im, new_box)
#     return im
#
# # scales region in im by x times horizontally and y times vertically
# def scale_region(im, box, x, y, fix_top = False, fix_bottom = False, fix_left = False, fix_right = False):
#     x1, y1, x2, y2 = box
#     w = x2 - x1
#     h = y2 - y1
#
#     if fix_left:
#         new_x1 = x1
#         new_x2 = int(x1 + w*x)
#     elif fix_right:
#         print("hello")
#         new_x1 = int(x2 - w*x)
#         new_x2 = x2
#     else:
#         cx = (x1 + x2) / 2
#         new_x1 = int(cx - w*x/2)
#         new_x2 = int(cx + w*x/2)
#
#     if fix_top:
#         new_y1 = y1
#         new_y2 = int(y1 + h*y)
#     elif fix_bottom:
#         new_y1 = int(y2 - h*y)
#         new_y2 = y2
#     else:
#         cy = (y1 + y2) / 2
#         new_y1 = int(cy - h*y/2)
#         new_y2 = int(cy + h*y/2)
#
#     new_w = new_x2 - new_x1
#     new_h = new_y2 - new_y1
#     new_box = (new_x1, new_y1, new_x2, new_y2)
#     new_im = im.crop(box)
#     new_im = new_im.resize((new_w, new_h))
#
#     draw = ImageDraw.Draw(im)
#     draw.rectangle(box, fill=(255, 255, 255, 0))
#     im.paste(new_im, new_box)
#     return im

class Block:
    # each block contains its original box and its new quad that it transforms to
    def __init__(self, im, box, quad):
        self.im = im
        self.box = box
        self.quad = quad
    # get bounding box
    def get_bb(self):
        (tl_x, tl_y), (tr_x, tr_y), (bl_x, bl_y), (br_x, br_y) = self.quad
        l = math.floor(min(tl_x, tr_x, bl_x, br_x))
        t = math.floor(min(tl_y, tr_y, bl_y, br_y))
        r = math.ceil(max(tl_x, tr_x, bl_x, br_x))
        b = math.ceil(max(tl_y, tr_y, bl_y, br_y))
        return l, t, r, b

# split im into blocks
# box is the bounding box (location) of im
def split(canvas, im, box, rows, cols):
    assert(rows <= im.height and cols <= im.width)
    l, t, r, b = box
    W, H = canvas.size
    w, h = im.size
    blocks = []
    for i in range(rows):
        for j in range(cols):
            block_l = l + w * j // cols
            block_t = t + h * i // rows
            if (j < cols - 1):
                block_r = l + w * (j+1) // cols
            else:
                block_r = r
            if (i < rows - 1):
                block_b = t + h * (i+1) // rows
            else:
                block_b = b
            block_box = (block_l, block_t, block_r, block_b)
            block_quad = ((block_l, block_t), (block_r, block_t),
                          (block_r, block_b), (block_l, block_b))
            block_im = Image.new('RGBA', (W, H), (255, 255, 255, 0))
            block_im.paste(im.crop((block_l-l, block_t-t, block_r-l, block_b-t)), block_box)
            block = Block(block_im, block_box, block_quad)
            blocks.append(block)
    return blocks

# transform the blocks to their new quads and draw them on canvas
def merge(canvas, blocks):
    for block in blocks:
        w, h = canvas.size
        im, (l, t, r, b), quad = block.im, block.box, block.quad
        old_quad = ((l, t), (r, t), (r, b), (l, b))
        (new_l, new_t, new_r, new_b) = union_boxes([block.get_bb(), block.box])
        coeffs = find_coeffs(quad, old_quad)
        new_im = im.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
        canvas.paste(new_im, (0, 0, w, h), new_im)

# rotate point around center counterclockwise by theta degrees
def rotate_point(point, center, theta):
    theta = theta * math.pi / 180
    x, y = point
    cx, cy = center
    cos = math.cos(theta)
    sin = math.sin(theta)
    new_x = cx + cos * (x - cx) - sin * (y - cy)
    new_y = cy + sin * (x - cx) + cos * (y - cy)
    return new_x, new_y

# stat is the stationary point/line when squetching
# if linear, stat is a line (tuple of two points), else stat is a point
# squetch quad by factor times, with stat stationary
def squetch_quad(quad, stat, factor, linear=True):
    new_quad = ()
    if linear:
        (x1, y1), (x2, y2) = stat
        for point in quad:
            x, y = point
            k = ((y2-y1) * (x-x1) - (x2-x1) * (y-y1)) / ((y2-y1)**2 + (x2-x1)**2)
            perp_x = x - k * (y2-y1)
            perp_y = y + k * (x2-x1)
            new_x = perp_x + (x - perp_x) * factor
            new_y = perp_y + (y - perp_y) * factor
            new_quad = new_quad + ((new_x, new_y),)
    else:
        px, py = stat
        for point in quad:
            x, y = point
            dx = x - px
            dy = y - py
            new_x = px + dx * factor
            new_y = py + dy * factor
            new_quad = new_quad + ((new_x, new_y),)
    return new_quad

# sample (x, y) in im
def sample_image(im, box, x, y):
    l, t, r, b = box
    if x < l-0.5 or x > r-0.5 or y < t+0.5 or y > b+0.5:
        return 255, 255, 255, 0
    if x == int(x) and y == int(y):
        return im.getpixel((x, y))

    if x == int(x):
        pixel1 = im.getpixel((x, math.floor(y)))
        pixel2 = im.getpixel((x, math.ceil(y)))
        r1, g1, b1, a1 = pixel1
        r2, g2, b2, a2 = pixel2
        w1, w2 = math.ceil(y) - y, y - math.floor(y)
        return int(w1*r1 + w2*r2), int(w1*g1 + w2*g2), int(w1*b1 + w2*b2), int(w1*a1 + w2*a2)
    elif y == int(y):
        pixel1 = im.getpixel((math.floor(x), y))
        pixel2 = im.getpixel((math.ceil(x), y))
        r1, g1, b1, a1 = pixel1
        r2, g2, b2, a2 = pixel2
        w1, w2 = math.ceil(x) - x, x - math.floor(x)
        return int(w1*r1 + w2*r2), int(w1*g1 + w2*g2), int(w1*b1 + w2*b2), int(w1*a1 + w2*a2)
    else:
        pixel1 = im.getpixel((math.floor(x), math.floor(y)))
        pixel2 = im.getpixel((math.floor(x), math.ceil(y)))
        pixel3 = im.getpixel((math.ceil(x), math.floor(y)))
        pixel4 = im.getpixel((math.ceil(x), math.ceil(y)))
        r1, g1, b1, a1 = pixel1
        r2, g2, b2, a2 = pixel2
        r3, g3, b3, a3 = pixel3
        r4, g4, b4, a4 = pixel4
        w1 = (math.ceil(x) - x) * (math.ceil(y) - y)
        w2 = (math.ceil(x) - x) * (y - math.floor(y))
        w3 = (x - math.floor(x)) * (math.ceil(y) - y)
        w4 = (x - math.floor(x)) * (y - math.floor(y))
        return (int(w1*r1 + w2*r2 + w3*r3 + w4*r4), int(w1*g1 + w2*g2 + w3*g3 + w4*g4),
                int(w1*b1 + w2*b2 + w3*b3 + w4*b4), int(w1*a1 + w2*a2 + w3*a3 + w4*a4))

# # map a point in quad to a point in box
# def map_quad_to_box(quad, box):
#     (tl_x, tl_y), (tr_x, tr_y), (bl_x, bl_y), (br_x, br_y) = quad
#     t_vector = (tr_x-tl_x, tr_y-tl_y)
#     l_vector = ()
#     return

# draw im on a quadrilateral defined by four points (tl, tr, bl, br)
# def draw_quad(im, box, quad):
#     (tl_x, tl_y), (tr_x, tr_y), (bl_x, bl_y), (br_x, br_y) = quad
#     new_l = math.floor(min(tl_x, tr_x, bl_x, br_x))
#     new_t = math.floor(min(tl_y, tr_y, bl_y, br_y))
#     new_r = math.ceil(max(tl_x, tr_x, bl_x, br_x))
#     new_b = math.ceil(max(tl_y, tr_y, bl_y, br_y))
#     new_box = (new_l, new_t, new_r, new_b)
#     new_w = new_r - new_l
#     new_h = new_b - new_t
#
#     for row in range(new_h):
#         for col in range(new_w):
#             for r in range(2):
#                 for c in range(2):
#                     new_x = new_l + col + 0.5*c - 0.25
#                     new_y = new_t + row + 0.5*r - 0.25
#                     point = (new_x, new_y)
#                     if point.within(Polygon(quad)):
#
#                         sample_image(im, box, x, y)

# find the coefficients of transforming from quad pb to quad pa
# reference: https://stackoverflow.com/questions/14177744/how-does-perspective-transformation-work-in-pil
def find_coeffs(pa, pb):
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])

    A = np.matrix(matrix, dtype=np.float)
    B = np.array(pb).reshape(8)

    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)