"""Panoramic App Store / Google Play screenshot engine.

One continuous canvas is designed and sliced into N store screenshots. Phones can straddle
panel boundaries and stickers can cross scenes, so swiping through the store listing feels
like one seamless picture.

Coordinates: x is given in PANEL UNITS (0.5 = centre of panel 1, 1.0 = boundary between
panels 1 and 2), y in pixels of the design size (default 1320x2868, iPhone 6.9").
"""
import json
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import emoji3d

PKG = os.path.dirname(os.path.abspath(__file__))
FONT_HEAD = os.path.join(PKG, "fonts", "Manrope-ExtraBold.ttf")
FONT_UI = os.path.join(PKG, "fonts", "Manrope-Bold.ttf")

# Apple screenshot sizes (portrait). Upload the largest your App Store Connect asks for.
SIZES = {
    "iphone-6.9": (1320, 2868),
    "iphone-6.7": (1290, 2796),
    "iphone-6.5": (1284, 2778),
    "iphone-5.5": (1242, 2208),
    "android-phone": (1080, 2340),
}


def _rgba(h, a=255):
    h = h.lstrip("#")
    if len(h) == 8:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def _font(path, size):
    return ImageFont.truetype(path, size)


class Panorama:
    def __init__(self, cfg: dict, base_dir: str = "."):
        self.cfg = cfg
        self.base = base_dir
        c = cfg.get("canvas", {})
        self.pw = int(c.get("panel_width", 1320))
        self.ph = int(c.get("panel_height", 2868))
        self.n = int(c.get("panels", 6))
        self.w = self.pw * self.n
        self.seed = int(c.get("seed", 7))
        f = cfg.get("fonts", {})
        self.font_head = self._path(f.get("headline")) or FONT_HEAD
        self.font_ui = self._path(f.get("ui")) or FONT_UI
        self.warnings = []
        self._head_boxes = {}  # panel -> (x0, y0, x1, y1)

    # ------------------------------------------------------------------ helpers
    def _path(self, p):
        if not p:
            return None
        return p if os.path.isabs(p) else os.path.join(self.base, p)

    def X(self, units):
        return int(round(float(units) * self.pw))

    def warn(self, msg):
        self.warnings.append(msg)

    # --------------------------------------------------------------- background
    def background(self):
        bg_cfg = self.cfg.get("background", {})
        scenes = bg_cfg.get("scenes") or [{"panels": [0, self.n - 1], "colors": ["#7A5CFA", "#4B2FD6"]}]
        tp = int(bg_cfg.get("transition_px", 70))
        stops = []
        for i, s in enumerate(scenes):
            a, b = s["panels"]
            x0, x1 = a * self.pw, (b + 1) * self.pw
            ca, cb = s["colors"][0], s["colors"][-1]
            stops.append((x0 + (tp if i else 0), _rgba(ca)[:3]))
            stops.append((x1 - (tp if i < len(scenes) - 1 else 0), _rgba(cb)[:3]))
        stops.sort(key=lambda t: t[0])
        row = Image.new("RGB", (self.w, 1))
        px = row.load()
        j = 0
        for x in range(self.w):
            while j < len(stops) - 2 and x > stops[j + 1][0]:
                j += 1
            (x0, c0), (x1, c1) = stops[j], stops[j + 1]
            t = 0 if x <= x0 else 1 if x >= x1 else (x - x0) / (x1 - x0)
            t = t * t * (3 - 2 * t)
            px[x, 0] = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
        img = row.resize((self.w, self.ph)).convert("RGBA")

        # vertical shade (slightly darker bottom)
        shade = Image.new("RGBA", (1, self.ph))
        for y in range(self.ph):
            t = y / self.ph
            shade.putpixel((0, y), (10, 6, 30, int(70 * max(0, t - 0.35) / 0.65)))
        img.alpha_composite(shade.resize((self.w, self.ph)))

        rnd = random.Random(self.seed)
        if bg_cfg.get("glow", True):
            glow = Image.new("RGBA", (self.w, self.ph), (0, 0, 0, 0))
            g = ImageDraw.Draw(glow)
            for _ in range(self.n * 2):
                cx, cy = rnd.randint(0, self.w), rnd.randint(200, self.ph - 200)
                r = rnd.randint(380, 700)
                g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 34))
            img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
        if bg_cfg.get("confetti", True):
            conf = Image.new("RGBA", (self.w, self.ph), (0, 0, 0, 0))
            c = ImageDraw.Draw(conf)
            for _ in range(self.n * 28):
                x, y = rnd.randint(0, self.w), rnd.randint(120, self.ph - 120)
                s = rnd.randint(10, 26)
                col = rnd.choice([(255, 255, 255, 70), (255, 214, 102, 90), (255, 255, 255, 45)])
                if rnd.random() < 0.5:
                    c.ellipse([x, y, x + s, y + s], fill=col)
                else:
                    c.rounded_rectangle([x, y, x + s * 2, y + s * 0.8], radius=s // 3, fill=col)
            img.alpha_composite(conf)
        return img

    # ----------------------------------------------------------------- headline
    def headline(self, cv, h):
        d = ImageDraw.Draw(cv)
        panel = int(h["panel"])
        lines = h["lines"]
        cx = panel * self.pw + self.pw // 2
        margin = int(h.get("margin", 75))
        size = int(h.get("size", 152))
        min_size = int(h.get("min_size", 84))
        while size > min_size and max(_font(self.font_head, size).getlength(l) for l in lines) > self.pw - 2 * margin:
            size -= 2
        f = _font(self.font_head, size)
        if max(f.getlength(l) for l in lines) > self.pw - 2 * margin:
            self.warn(f"panel {panel + 1}: headline too long even at {size}px — shorten it")
        pill = h.get("pill_line")
        pill_bg = h.get("pill_color", "#FFFFFF")
        pill_fg = h.get("pill_text", "#1A1033")
        color = h.get("color", "#FFFFFF")
        y = int(h.get("y", 300))
        top = y
        widest = 0
        for i, line in enumerate(lines):
            tw = f.getlength(line)
            widest = max(widest, tw + (60 if i == pill else 0))
            if i == pill:
                # room for descenders of the previous line (ş, g, ç, y …)
                y += int(size * 0.10)
                d.rounded_rectangle([cx - tw / 2 - 30, y - 6, cx + tw / 2 + 30, y + size * 1.16],
                                    radius=int(size * 0.32), fill=_rgba(pill_bg))
                d.text((cx - tw / 2, y), line, font=f, fill=_rgba(pill_fg))
            else:
                sh = Image.new("RGBA", (int(tw) + 80, size + 80), (0, 0, 0, 0))
                ImageDraw.Draw(sh).text((40, 30), line, font=f, fill=(20, 8, 60, 120))
                cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (int(cx - tw / 2 - 40), int(y - 22)))
                d.text((cx - tw / 2, y), line, font=f, fill=_rgba(color))
            y += int(size * 1.28)
        self._head_boxes[panel] = (cx - widest / 2, top - 10, cx + widest / 2, y)

    def brand(self, cv, b):
        x = self.X(b.get("x", 0.09))
        y = int(b.get("y", 120))
        s = int(b.get("icon_size", 120))
        if b.get("icon"):
            icon = Image.open(self._path(b["icon"])).convert("RGBA").resize((s, s), Image.LANCZOS)
            m = Image.new("L", (s, s), 0)
            ImageDraw.Draw(m).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.23), fill=255)
            icon.putalpha(m)
            cv.alpha_composite(icon, (x, y))
            x += s + 26
        if b.get("name"):
            ImageDraw.Draw(cv).text((x, y + int(s * 0.18)), b["name"], font=_font(self.font_head, int(s * 0.53)),
                                    fill=_rgba(b.get("color", "#FFFFFF")))

    # -------------------------------------------------------------------- phone
    def _status_bar(self, scr, p):
        scr = scr.convert("RGBA")
        d = ImageDraw.Draw(scr)
        w = scr.size[0]
        k = w / 1170  # tuned for 1170 px wide screenshots
        fg = p.get("status_color", "#FFFFFF")
        d.text((118 * k, 52 * k), p.get("time", "9:41"), font=_font(self.font_ui, int(50 * k)), fill=fg)
        d.rounded_rectangle([w / 2 - 190 * k, 30 * k, w / 2 + 190 * k, 140 * k], radius=55 * k, fill="black")
        bx = w - 330 * k
        for i in range(4):
            hh = (14 + i * 8) * k
            d.rounded_rectangle([bx + i * 18 * k, 92 * k - hh, bx + i * 18 * k + 12 * k, 92 * k], radius=3 * k, fill=fg)
        cx, cy = w - 220 * k, 94 * k
        for r in (34, 22, 10):
            d.arc([cx - r * k, cy - r * k, cx + r * k, cy + r * k], 225, 315, fill=fg, width=max(2, int(8 * k)))
        d.rounded_rectangle([w - 172 * k, 58 * k, w - 92 * k, 96 * k], radius=10 * k, outline=fg, width=max(2, int(4 * k)))
        d.rounded_rectangle([w - 166 * k, 64 * k, w - 106 * k, 90 * k], radius=6 * k, fill=fg)
        d.rounded_rectangle([w - 88 * k, 70 * k, w - 82 * k, 84 * k], radius=2 * k, fill=fg)
        return scr

    def phone_image(self, p):
        scr = Image.open(self._path(p["screen"])).convert("RGBA")
        if p.get("status_bar", "draw") == "draw":
            scr = self._status_bar(scr, p)
        sw = int(p.get("width", 880))
        sh = int(sw * scr.size[1] / scr.size[0])
        if scr.size[0] < sw * 0.95:
            self.warn(f'{p["screen"]}: source {scr.size[0]}px is upscaled to {sw}px — capture at 3x for sharpness')
        scr = scr.resize((sw, sh), Image.LANCZOS)
        bez, rad = int(sw * 0.038), int(sw * 0.135)
        W, H = sw + bez * 2, sh + bez * 2
        body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(body)
        frame = p.get("frame_color", "#1A1824")
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=rad + bez, fill=_rgba(frame))
        d.rounded_rectangle([3, 3, W - 4, H - 4], radius=rad + bez - 3, outline=(120, 116, 140, 255), width=4)
        d.rounded_rectangle([bez - 6, bez - 6, W - bez + 5, H - bez + 5], radius=rad + 6, fill=(6, 6, 10, 255))
        m = Image.new("L", (sw, sh), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, sw - 1, sh - 1], radius=rad, fill=255)
        body.paste(scr, (bez, bez), m)
        d.rounded_rectangle([-6, int(H * 0.22), 4, int(H * 0.29)], radius=4, fill=(40, 38, 52, 255))
        d.rounded_rectangle([W - 4, int(H * 0.26), W + 6, int(H * 0.36)], radius=4, fill=(40, 38, 52, 255))
        ang = float(p.get("angle", 0))
        return body.rotate(ang, resample=Image.BICUBIC, expand=True) if ang else body

    def sticker_image(self, s):
        if s.get("image"):
            src = Image.open(self._path(s["image"])).convert("RGBA")
        else:
            src = Image.open(emoji3d.fetch(s["emoji"])).convert("RGBA")
        size = int(s.get("size", 320))
        if size > src.size[0] * 1.7:
            self.warn(f'sticker "{s.get("emoji") or s.get("image")}": {size}px from a {src.size[0]}px source will look soft')
        im = src.resize((size, size), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
        ang = float(s.get("angle", 0))
        return im.rotate(ang, resample=Image.BICUBIC, expand=True) if ang else im

    def drop(self, cv, img, cx, cy, shadow=True):
        x, y = int(cx - img.size[0] / 2), int(cy - img.size[1] / 2)
        if shadow:
            a = img.split()[3].point(lambda v: int(v * 0.55))
            sh = Image.new("RGBA", img.size, (8, 4, 30, 0))
            sh.putalpha(a)
            cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(38)), (x + 26, y + 46))
        cv.alpha_composite(img, (x, y))
        return (x, y, x + img.size[0], y + img.size[1])

    # --------------------------------------------------------------- validation
    def _check_overlap(self, kind, name, box, tolerance=24):
        x0, y0, x1, y1 = box
        for panel, (hx0, hy0, hx1, hy1) in self._head_boxes.items():
            ox = min(x1, hx1) - max(x0, hx0)
            oy = min(y1, hy1) - max(y0, hy0)
            if ox > tolerance and oy > tolerance:
                self.warn(f"{kind} {name} overlaps the headline of panel {panel + 1} by {int(oy)}px vertically")

    # ------------------------------------------------------------------- render
    def render(self):
        cv = self.background()
        for h in self.cfg.get("headlines", []):
            self.headline(cv, h)
        if self.cfg.get("brand"):
            self.brand(cv, self.cfg["brand"])
        items = [("phone", p, int(p.get("z", 10))) for p in self.cfg.get("phones", [])]
        items += [("sticker", s, int(s.get("z", 20))) for s in self.cfg.get("stickers", [])]
        for kind, it, _ in sorted(items, key=lambda t: t[2]):
            img = self.phone_image(it) if kind == "phone" else self.sticker_image(it)
            box = self.drop(cv, img, self.X(it["x"]), int(it["y"]), shadow=it.get("shadow", True))
            name = it.get("screen") or it.get("emoji") or it.get("image")
            self._check_overlap(kind, name, box)
        # empty-looking panels
        for i in range(self.n):
            if i not in self._head_boxes:
                self.warn(f"panel {i + 1} has no headline — every panel should say something on its own")
        return cv

    def save(self, out_dir, sizes=None, preview=True):
        sizes = sizes or self.cfg.get("output", {}).get("sizes") or ["iphone-6.9", "iphone-6.5"]
        cv = self.render().convert("RGB")
        written = []
        for name in sizes:
            size = tuple(SIZES[name]) if isinstance(name, str) else tuple(name)
            label = name if isinstance(name, str) else f"{size[0]}x{size[1]}"
            d = os.path.join(out_dir, label)
            os.makedirs(d, exist_ok=True)
            for f in os.listdir(d):
                if f.endswith(".png"):
                    os.remove(os.path.join(d, f))
            for i in range(self.n):
                p = cv.crop((i * self.pw, 0, (i + 1) * self.pw, self.ph))
                if size != (self.pw, self.ph):
                    p = p.resize(size, Image.LANCZOS)
                fp = os.path.join(d, f"{i + 1:02d}.png")
                p.save(fp, optimize=True)
                written.append(fp)
        if preview:
            cv.resize((self.w // 8, self.ph // 8), Image.LANCZOS).save(os.path.join(out_dir, "_preview_panorama.png"))
            tw, th = 330, int(330 * self.ph / self.pw)
            sheet = Image.new("RGB", (self.n * (tw + 8), th), "white")
            for i in range(self.n):
                sheet.paste(cv.crop((i * self.pw, 0, (i + 1) * self.pw, self.ph)).resize((tw, th), Image.LANCZOS),
                            (i * (tw + 8), 0))
            sheet.save(os.path.join(out_dir, "_preview_panels.png"))
        return written


def load(path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    return Panorama(cfg, base_dir=os.path.dirname(os.path.abspath(path)))
