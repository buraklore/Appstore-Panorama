"""Generates 3 placeholder app screens (1170x2532) for the demo — replace with REAL captures."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "..", "..", "panorama", "fonts", "Manrope-ExtraBold.ttf")
FB = os.path.join(HERE, "..", "..", "panorama", "fonts", "Manrope-Bold.ttf")
W, H = 1170, 2532
BG, CARD, TXT, MUT = (14, 22, 18), (26, 38, 32), (236, 248, 240), (150, 172, 160)
ACC = [(76, 217, 138), (255, 196, 64), (90, 170, 255), (255, 120, 120)]


def f(p, s):
    return ImageFont.truetype(p, s)


def base(title):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((70, 190), title, font=f(F, 92), fill=TXT)
    return im, d


def home():
    im, d = base("My plants")
    for i, (n, s) in enumerate([("Monstera", "Water today"), ("Fiddle leaf", "In 2 days"),
                                ("Snake plant", "In 5 days"), ("Pothos", "Fertilize Sunday")]):
        y = 380 + i * 330
        d.rounded_rectangle([60, y, W - 60, y + 290], radius=48, fill=CARD)
        d.ellipse([100, y + 45, 300, y + 245], fill=ACC[i])
        d.text((340, y + 70), n, font=f(F, 64), fill=TXT)
        d.text((340, y + 160), s, font=f(FB, 46), fill=MUT)
    d.rounded_rectangle([60, H - 330, W - 60, H - 190], radius=60, fill=ACC[0])
    d.text((W / 2, H - 260), "+ Add a plant", font=f(F, 56), fill=BG, anchor="mm")
    return im


def stats():
    im, d = base("Growth")
    vals = [30, 45, 40, 62, 70, 66, 88]
    for i, v in enumerate(vals):
        x = 110 + i * 140
        d.rounded_rectangle([x, 1300 - v * 9, x + 90, 1300], radius=30, fill=ACC[2] if i == 6 else CARD)
    d.text((70, 1400), "+38% healthier", font=f(F, 84), fill=ACC[0])
    d.text((70, 1520), "than last month", font=f(FB, 54), fill=MUT)
    for i, t in enumerate(["7-day streak", "12 plants", "3 rooms"]):
        y = 1700 + i * 210
        d.rounded_rectangle([60, y, W - 60, y + 170], radius=40, fill=CARD)
        d.text((110, y + 55), t, font=f(F, 58), fill=TXT)
    return im


def reminder():
    im, d = base("Reminders")
    for i, (t, s, c) in enumerate([("Water Monstera", "08:00 · every 4 days", 0), ("Mist ferns", "10:30 · daily", 2),
                                   ("Rotate cactus", "Sat · weekly", 1), ("Repot pothos", "Next month", 3)]):
        y = 380 + i * 300
        d.rounded_rectangle([60, y, W - 60, y + 260], radius=48, fill=CARD)
        d.rounded_rectangle([W - 270, y + 90, W - 110, y + 170], radius=40, fill=ACC[c])
        d.text((110, y + 60), t, font=f(F, 60), fill=TXT)
        d.text((110, y + 150), s, font=f(FB, 44), fill=MUT)
    return im


if __name__ == "__main__":
    out = os.path.join(HERE, "screens")
    os.makedirs(out, exist_ok=True)
    for n, fn in (("01", home), ("02", stats), ("03", reminder)):
        fn().save(os.path.join(out, n + ".png"))
    print("✓ demo screens →", out)
