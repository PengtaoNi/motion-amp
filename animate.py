import image_ops
import frame_ops
from PIL import Image
import math
import os
# import cv2
# import numpy as np
# import matplotlib.pyplot as plt

#########
# SETUP #
#########
rope = Image.open("rope.png")
body = Image.open("body.png")
canvas = Image.new('RGBA', (1200, 1200), (200, 200, 200, 255))
canvas_box = (0, 0, 1200, 1200)

rope_w, rope_h = rope.size
body_w, body_h = body.size
w, h = canvas.size

rope_box = (511, 19, 564, 357)
body_box = (197, 338, 1002, 774)
rope_blocks = image_ops.split(canvas, rope, rope_box, 6, 1)
body_blocks = image_ops.split(canvas, body, body_box, 4, 4)

# rotate_frames = frame_ops.make_frames(20, rope=rope_blocks, body=body_blocks)
# bounce_frames = frame_ops.make_frames(20 , rope=rope_blocks, body=body_blocks)
bend_frames = frame_ops.make_frames(2, rope=rope_blocks, body=body_blocks)


###################
# TRANSFORMATIONS #
###################
# rotate_frames = frame_ops.rotate(rotate_frames, "rope", (536, 20), [30, 18, 6, -4, -12, -20, -12, -4, 2, 6, 12, 6, 2, -1, -3, -5, -3, -1, 1, 0])
# rotate_frames = frame_ops.rotate(rotate_frames, "body", (536, 20), [30, 18, 6, -4, -12, -20, -12, -4, 2, 6, 12, 6, 2, -1, -3, -5, -3, -1, 1, 0])

# ds = []
# disps = []
# rope_factors = []
# body_factors = []
# inv_body_factors = []
# for x in range(20):
#     h = math.exp(-x/6) * math.cos(x) * 200
#     d = 200 - h
#     disp = (0, d)
#     rope_factor = (rope_h + d) / rope_h
#     body_factor = 0.4 * (0.5 - math.fabs(h/200)) + 1
#     inv_body_factor = 1/body_factor
#     disps.append(disp)
#     rope_factors.append(rope_factor)
#     inv_body_factors.append(inv_body_factor)
#     body_factors.append(body_factor)
# bounce_frames = frame_ops.squetch(bounce_frames, "body", ((0, 338), (1, 338)), body_factors)
# bounce_frames = frame_ops.squetch(bounce_frames, "body", ((600, 0), (600, 1)), inv_body_factors)
# bounce_frames = frame_ops.squetch(bounce_frames, "rope", ((0, 19), (1, 19)), rope_factors)
# bounce_frames = frame_ops.translate(bounce_frames, "body", disps)

bend_frames = frame_ops.bend(bend_frames, "body", [[(187,556), (500,520), (700,520), (1002,556)], [(187,556), (500,520), (700,520), (1002,556)]])

#################
# VISUALIZATION #
#################
# frame_ops.make_movie("rotate", rotate_frames)
# frame_ops.make_movie("bounce", bounce_frames)
frame_ops.make_movie("bend", bend_frames)

# from scipy import interpolate
# import numpy as np
# import matplotlib.pyplot as plt
#
# tck, u = interpolate.splprep([[0, 1, 2, 3, 4], [1, 1.2, 1, 0.8, 1]], k=4)
# unew = np.arange(0, 1.01, 0.01)
# out = interpolate.splev(unew, tck)
# plt.plot(out[0], out[1])
# print(interpolate.splev(unew, tck, der=1))
# plt.show()