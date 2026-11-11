# Draws the FindCurves Studio icon - data points with a smooth curve fitted
# through them - and saves it in the formats each platform needs:
#
#   icons/FindCurves.ico     Windows: the program, installer and windows
#   icons/FindCurves.icns    macOS: the application bundle
#   icons/FindCurves-N.png   window icons and the logo at N pixels, and the
#                            256 pixel version for Linux menus
#
# The icons are part of the source code; run this again only after changing
# the design:   python branding/MakeIcons.py
#
# Each size is drawn separately, four times larger and then reduced, so that
# small sizes get simpler, bolder artwork instead of a blurred large icon.

import math, os

from PIL import Image, ImageDraw

# brand colors, also used by Theme.py
backgroundTop = (26, 58, 82)     # deep blue-teal
backgroundBottom = (14, 33, 49)
curveColor = (63, 209, 184)      # teal - the fitted curve
pointColor = (247, 178, 66)      # amber - the data points
axisColor = (93, 126, 150)

sizes = [16, 24, 32, 48, 64, 128, 256, 512, 1024]
folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icons')


def Curve(t):
    # an S-shaped curve rising across the icon, t and the result from 0 to 1
    return 1.0 / (1.0 + math.exp(-9.0 * (t - 0.5)))


def Draw(size):
    scale = 4
    s = size * scale
    image = Image.new('RGBA', (s, s), (0, 0, 0, 0))

    # rounded square with a vertical gradient
    gradient = Image.new('RGBA', (s, s))
    for row in range(s):
        f = row / (s - 1)
        gradient.paste(tuple(int(a + (b - a) * f) for a, b in zip(backgroundTop, backgroundBottom)) + (255,),
                       (0, row, s, row + 1))
    mask = Image.new('L', (s, s), 0)
    inset = 0 if size <= 24 else s * 0.03
    ImageDraw.Draw(mask).rounded_rectangle((inset, inset, s - 1 - inset, s - 1 - inset), radius=s * 0.22, fill=255)
    image.paste(gradient, (0, 0), mask)
    draw = ImageDraw.Draw(image)

    # the plot area
    left, right = s * 0.20, s * 0.84
    top, bottom = s * 0.18, s * 0.80
    def Point(t, value):
        return (left + t * (right - left), bottom - value * (bottom - top))

    # axes, at larger sizes only
    if size >= 48:
        width = max(1, round(s * 0.018))
        draw.line([(left - s * 0.04, top - s * 0.02), (left - s * 0.04, bottom + s * 0.04),
                   (right + s * 0.02, bottom + s * 0.04)], fill=axisColor + (255,), width=width, joint='curve')

    # the fitted curve
    width = s * (0.085 if size <= 24 else 0.065)
    points = [Point(i / 80.0, Curve(i / 80.0)) for i in range(81)]
    draw.line(points, fill=curveColor + (255,), width=round(width), joint='curve')
    for end in (points[0], points[-1]): # rounded ends
        r = width / 2
        draw.ellipse((end[0] - r, end[1] - r, end[0] + r, end[1] + r), fill=curveColor + (255,))

    # the data points, scattered either side of the curve
    if size <= 24:
        data = [(0.10, -0.14), (0.50, 0.17), (0.90, -0.14)]
        radius = s * 0.095
    else:
        data = [(0.04, 0.09), (0.24, -0.10), (0.42, 0.13), (0.58, -0.12), (0.76, 0.10), (0.96, -0.08)]
        radius = s * 0.058
    for t, offset in data:
        x, y = Point(t, Curve(t) + offset)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=pointColor + (255,),
                     outline=backgroundBottom + (255,), width=max(1, round(s * 0.012)))

    return image.resize((size, size), Image.LANCZOS)


if __name__ == '__main__':
    os.makedirs(folder, exist_ok=True)
    images = {size: Draw(size) for size in sizes}
    for size in [16, 24, 32, 48, 64, 256]:
        images[size].save(os.path.join(folder, 'FindCurves-%d.png' % size))
    icoSizes = [16, 24, 32, 48, 64, 128, 256]
    images[256].save(os.path.join(folder, 'FindCurves.ico'), format='ICO',
                     sizes=[(n, n) for n in icoSizes], append_images=[images[n] for n in icoSizes if n != 256])
    icnsSizes = [16, 32, 64, 128, 256, 512, 1024]
    images[1024].save(os.path.join(folder, 'FindCurves.icns'), format='ICNS',
                      append_images=[images[n] for n in icnsSizes if n != 1024])
    print('saved icons in', os.path.normpath(folder))
