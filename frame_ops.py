import image_ops
from PIL import Image, ImageDraw
from scipy import interpolate
import os

# input kwargs contains blocks of regions that we want to keep track of
# each frame is a dict that contains all the blocks
def make_frame(**kwargs):
    frame = {}
    boxes = []
    for region, blocks in kwargs.items():
        new_blocks = []
        for row in blocks:
            new_row = []
            for block in row:
                new_row.append(image_ops.Block(block.im, block.box, block.quad))
            new_blocks.append(new_row)
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
        for row in blocks:
            for block in row:
                (tl_x, tl_y), (tr_x, tr_y), (bl_x, bl_y), (br_x, br_y) = block.quad
                block.quad = (tl_x+dx, tl_y+dy), (tr_x+dx, tr_y+dy), (bl_x+dx, bl_y+dy), (br_x+dx, br_y+dy)
    return frames

# rotates the region around center by theta degrees counterclockwise
def rotate(frames, region, center, thetas):
    for i in range(len(frames)):
        frame = frames[i]
        theta = thetas[i]
        blocks = frame[region]
        for row in blocks:
            for block in row:
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
        for row in blocks:
            for block in row:
                block.quad = image_ops.squetch_quad(block.quad, stat, factor)
    return frames

# bends the region following a curve that interpolates the crv_pts
# ignores transformations applied before this
def bend(frames, region, crv_pts_list):
    for i in range(len(frames)):
        frame = frames[i]
        crv_pts = crv_pts_list[i]

        x_pts, y_pts = [], []
        for crv_pt in crv_pts:
            x_pts.append(crv_pt[0])
            y_pts.append(crv_pt[1])
        n_pts = len(x_pts)
        if n_pts < 2:
            continue
        degree = min(n_pts-1, 3)
        tck, u = interpolate.splprep([x_pts, y_pts], s=0, k=degree)

        blocks = frame[region]
        block_h = blocks[0][0].box[3] - blocks[0][0].box[1]
        n_rows = len(blocks)
        n_cols = len(blocks[0])
        new_u = [i / n_cols for i in range(n_cols+1)]
        new_x = interpolate.splev(new_u, tck)[0]
        new_y = interpolate.splev(new_u, tck)[1]
        slopes = interpolate.splev(new_u, tck, der=1)
        slope_x = slopes[0]
        slope_y = slopes[1]

        if n_rows % 2 == 0:
            for i in range(n_rows):
                row = blocks[i]
                d = i - (n_rows / 2 - 1) # number of rows away from the center row
                for j in range(n_cols):
                    block = row[j]
                    slope1 = slope_y[j] / slope_x[j]
                    slope2 = slope_y[j+1] / slope_x[j+1]
                    norm1 = -1 / slope1
                    norm2 = -1 / slope2
                    unit_norm_v1 = (1 / (1 + norm1 ** 2) ** 0.5, norm1 / (1 + norm1 ** 2) ** 0.5)
                    unit_norm_v2 = (1 / (1 + norm2 ** 2) ** 0.5, norm2 / (1 + norm2 ** 2) ** 0.5)
                    if slope1 < 0:
                        v1 = (unit_norm_v1[0] * block_h, unit_norm_v1[1] * block_h)
                    else:
                        v1 = (-unit_norm_v1[0] * block_h, -unit_norm_v1[1] * block_h)
                    if slope2 < 0:
                        v2 = (unit_norm_v2[0] * block_h, unit_norm_v2[1] * block_h)
                    else:
                        v2 = (-unit_norm_v2[0] * block_h, -unit_norm_v2[1] * block_h)

                    bl = (new_x[j] + v1[0] * d, new_y[j] + v1[1] * d)
                    br = (new_x[j+1] + v2[0] * d, new_y[j+1] + v2[1] * d)
                    tl = (bl[0] - v1[0], bl[1] - v1[1])
                    tr = (br[0] - v2[0], br[1] - v2[1])
                    block.quad = (tl, tr, br, bl)
                    print(block.quad)
        else:
            for i in range(n_rows):
                row = blocks[i]
                d = i - (n_rows / 2 - 1)
                for j in range(n_cols):
                    block = row[j]
                    slope1 = slope_y[j] / slope_x[j]
                    slope2 = slope_y[j+1] / slope_x[j+1]
                    norm1 = -1 / slope1
                    norm2 = -1 / slope2
                    unit_norm_v1 = (1 / (1 + norm1 ** 2) ** 0.5, norm1 / (1 + norm1 ** 2) ** 0.5)
                    unit_norm_v2 = (1 / (1 + norm2 ** 2) ** 0.5, norm2 / (1 + norm2 ** 2) ** 0.5)
                    if slope1 < 0:
                        v1 = (unit_norm_v1[0] * block_h, unit_norm_v1[1] * block_h)
                    else:
                        v1 = (-unit_norm_v1[0] * block_h, -unit_norm_v1[1] * block_h)
                    if slope2 < 0:
                        v2 = (unit_norm_v2[0] * block_h, unit_norm_v2[1] * block_h)
                    else:
                        v2 = (-unit_norm_v2[0] * block_h, -unit_norm_v2[1] * block_h)

                    bl = (new_x[j] + v1[0] * (d+0.5), new_y[j] + v1[1] * (d+0.5))
                    br = (new_x[j+1] + v2[0] * (d+0.5), new_y[j+1] + v2[1] * (d+0.5))
                    tl = (bl[0] - v1[0], bl[1] - v1[1])
                    tr = (br[0] - v2[0], br[1] - v2[1])
                    block.quad = (tl, tr, br, bl)
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