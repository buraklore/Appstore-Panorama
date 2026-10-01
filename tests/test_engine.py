"""Offline tests: python -m unittest discover tests"""
import os
import shutil
import tempfile
import unittest

from PIL import Image

from panorama.engine import Panorama


def _screen(path, color):
    Image.new("RGB", (1170, 2532), color).save(path)


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.dir, "screens"))
        _screen(os.path.join(self.dir, "screens", "a.png"), (30, 30, 40))
        Image.new("RGBA", (256, 256), (255, 80, 80, 255)).save(os.path.join(self.dir, "dot.png"))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def cfg(self, **over):
        c = {
            "canvas": {"panels": 2},
            "headlines": [
                {"panel": 0, "lines": ["Hello", "world"], "pill_line": 1},
                {"panel": 1, "lines": ["Şarkı söyle", "güzel ğüşiöç"], "pill_line": 1},
            ],
            "phones": [{"screen": "screens/a.png", "x": 1.0, "y": 1960, "width": 880, "angle": -5}],
            "stickers": [{"image": "dot.png", "x": 0.2, "y": 2300, "size": 300}],
        }
        c.update(over)
        return c

    def test_slices_and_sizes(self):
        p = Panorama(self.cfg(), self.dir)
        out = os.path.join(self.dir, "out")
        files = p.save(out, sizes=["iphone-6.9", "iphone-6.5"])
        self.assertEqual(len(files), 4)
        self.assertEqual(Image.open(os.path.join(out, "iphone-6.9", "01.png")).size, (1320, 2868))
        self.assertEqual(Image.open(os.path.join(out, "iphone-6.5", "02.png")).size, (1284, 2778))
        self.assertTrue(os.path.exists(os.path.join(out, "_preview_panels.png")))
        self.assertEqual(p.warnings, [])

    def test_phone_straddles_boundary(self):
        cv = Panorama(self.cfg(), self.dir).render()
        # pixels of the dark phone body must exist on BOTH sides of the 1|2 boundary
        y = 1960
        left, right = cv.getpixel((1320 - 200, y)), cv.getpixel((1320 + 200, y))
        self.assertLess(sum(left[:3]), 200)
        self.assertLess(sum(right[:3]), 200)

    def test_warns_on_long_headline(self):
        c = self.cfg(headlines=[{"panel": 0, "lines": ["This headline is far far far too long to fit any phone"]},
                                {"panel": 1, "lines": ["ok"]}])
        p = Panorama(c, self.dir)
        p.render()
        self.assertTrue(any("too long" in w for w in p.warnings), p.warnings)

    def test_warns_on_sticker_over_headline(self):
        c = self.cfg(stickers=[{"image": "dot.png", "x": 0.5, "y": 380, "size": 300}])
        p = Panorama(c, self.dir)
        p.render()
        self.assertTrue(any("overlaps the headline" in w for w in p.warnings), p.warnings)

    def test_warns_on_missing_headline_and_soft_sticker(self):
        c = self.cfg(headlines=[{"panel": 0, "lines": ["Only one"]}],
                     stickers=[{"image": "dot.png", "x": 0.2, "y": 2300, "size": 600}])
        p = Panorama(c, self.dir)
        p.render()
        self.assertTrue(any("panel 2 has no headline" in w for w in p.warnings), p.warnings)
        self.assertTrue(any("look soft" in w for w in p.warnings), p.warnings)


if __name__ == "__main__":
    unittest.main()
