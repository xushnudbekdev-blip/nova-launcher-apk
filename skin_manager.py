import os
import math
from PIL import Image, ImageDraw
from PyQt6.QtGui import QPixmap, QImage


class SkinManager:

    # ──────────────────────────────────────────────────────────────
    #  Preset Cape textures
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def get_preset_cape(preset_name):
        img  = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if preset_name == "preset_nova":
            draw.rectangle([0, 0, 63, 31], fill=(45, 15, 80, 255))
            draw.rectangle([1, 1, 62, 30], fill=(75, 25, 130, 255))
            draw.rectangle([4, 4, 18, 28], fill=(147, 51, 234, 255))
            draw.rectangle([6, 8, 16, 24], fill=(234, 179, 8, 255))
            draw.rectangle([9, 6, 13, 26], fill=(250, 204, 21, 255))
        elif preset_name == "preset_admin":
            draw.rectangle([0, 0, 63, 31], fill=(120, 10, 15, 255))
            draw.rectangle([1, 1, 62, 30], fill=(185, 28, 28, 255))
            draw.rectangle([2, 2, 20, 30], fill=(220, 38, 38, 255))
            draw.rectangle([4, 4, 18, 6],  fill=(251, 191, 36, 255))
            draw.rectangle([6, 12, 16, 22], fill=(251, 191, 36, 255))
            draw.rectangle([9, 8, 13, 26],  fill=(245, 158, 11, 255))
        elif preset_name == "preset_optifine":
            draw.rectangle([0, 0, 63, 31], fill=(180, 20, 20, 255))
            draw.rectangle([1, 1, 62, 30], fill=(220, 38, 38, 255))
            draw.rectangle([5, 8, 11, 24],  fill=(255, 255, 255, 255))
            draw.rectangle([7, 10, 9, 22],  fill=(220, 38, 38, 255))
            draw.rectangle([13, 8, 18, 24], fill=(255, 255, 255, 255))
            draw.rectangle([15, 10, 18, 12], fill=(220, 38, 38, 255))
            draw.rectangle([15, 14, 17, 16], fill=(220, 38, 38, 255))
        elif preset_name == "preset_minecon":
            draw.rectangle([0, 0, 63, 31], fill=(153, 27, 27, 255))
            draw.rectangle([6, 8, 8, 12],   fill=(30, 30, 30, 255))
            draw.rectangle([14, 8, 16, 12],  fill=(30, 30, 30, 255))
            draw.rectangle([8, 12, 14, 18],  fill=(30, 30, 30, 255))
            draw.rectangle([6, 14, 8, 20],   fill=(30, 30, 30, 255))
            draw.rectangle([14, 14, 16, 20], fill=(30, 30, 30, 255))
        return img

    # ──────────────────────────────────────────────────────────────
    #  Default Steve texture (64×64)
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def get_default_steve():
        """Generate a proper colorful Steve skin (64x64 RGBA)."""
        img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        SKIN  = (198, 152, 109, 255)
        HAIR  = ( 89,  57,  29, 255)
        EYE_W = (255, 255, 255, 255)
        EYE_B = ( 45,  80, 200, 255)
        MOUTH = (130,  80,  60, 255)
        SHIRT = (100, 100, 200, 255)
        SHRT2 = ( 80,  80, 170, 255)
        PANTS = ( 50,  60, 110, 255)
        BOOT  = ( 60,  40,  20, 255)
        ARM_S = (198, 152, 109, 255)
        ARM_H = (160, 115,  72, 255)

        # HEAD face (UV 8-16, 8-16)
        draw.rectangle([8,  8, 15, 15], fill=SKIN)
        draw.rectangle([8,  8, 15,  9], fill=HAIR)
        draw.rectangle([8,  8,  8, 15], fill=HAIR)
        draw.rectangle([15, 8, 15, 15], fill=HAIR)
        draw.rectangle([ 9, 11, 10, 12], fill=EYE_W)
        draw.rectangle([ 9, 11,  9, 11], fill=EYE_B)
        draw.rectangle([13, 11, 14, 12], fill=EYE_W)
        draw.rectangle([13, 11, 13, 11], fill=EYE_B)
        draw.rectangle([10, 14, 13, 14], fill=MOUTH)
        # HEAD top (UV 8-16, 0-8)
        draw.rectangle([8, 0, 15, 7], fill=HAIR)
        # HEAD sides
        draw.rectangle([ 0, 8,  7, 15], fill=SKIN)
        draw.rectangle([16, 8, 23, 15], fill=SKIN)
        draw.rectangle([24, 8, 31, 15], fill=HAIR)
        # Helmet overlay
        draw.rectangle([40, 8, 47, 15], fill=(89, 57, 29, 80))

        # TORSO (UV 20-28, 20-32)
        draw.rectangle([20, 20, 27, 31], fill=SHIRT)
        draw.rectangle([23, 20, 24, 31], fill=SHRT2)
        draw.rectangle([20, 16, 27, 19], fill=SHRT2)
        draw.rectangle([16, 20, 19, 31], fill=SHRT2)
        draw.rectangle([28, 20, 31, 31], fill=SHRT2)
        draw.rectangle([32, 20, 39, 31], fill=SHIRT)

        # RIGHT ARM (UV 44-48, 20-32)
        draw.rectangle([44, 20, 47, 31], fill=ARM_S)
        draw.rectangle([40, 20, 43, 31], fill=ARM_H)
        draw.rectangle([44, 16, 47, 19], fill=ARM_H)

        # LEFT ARM (UV 36-40, 52-64)
        draw.rectangle([36, 52, 39, 63], fill=ARM_H)
        draw.rectangle([40, 52, 43, 63], fill=ARM_S)
        draw.rectangle([40, 48, 43, 51], fill=ARM_H)

        # RIGHT LEG (UV 4-8, 20-32)
        draw.rectangle([ 4, 20,  7, 31], fill=PANTS)
        draw.rectangle([ 0, 20,  3, 31], fill=(40, 50, 90, 255))
        draw.rectangle([ 4, 16,  7, 19], fill=BOOT)
        draw.rectangle([ 4, 29,  7, 31], fill=BOOT)

        # LEFT LEG (UV 20-24, 52-64)
        draw.rectangle([20, 52, 23, 63], fill=PANTS)
        draw.rectangle([16, 52, 19, 63], fill=(40, 50, 90, 255))
        draw.rectangle([20, 48, 23, 51], fill=BOOT)
        draw.rectangle([20, 61, 23, 63], fill=BOOT)

        return img


    # ──────────────────────────────────────────────────────────────
    #  3-D Isometric Minecraft Character Renderer
    #
    #  Layout on a 160×320 canvas (FRONT or BACK view):
    #   - head   top face (isometric top)
    #   - head   front face
    #   - head   right side face (shaded)
    #   - torso, arms, legs — same treatment
    # ──────────────────────────────────────────────────────────────

    # ── tiny helpers ──────────────────────────────────────────────
    @staticmethod
    def _darken(color, factor=0.55):
        """Return an RGBA tuple darkened by factor (for 3-D side shading)."""
        r, g, b, a = color
        return (int(r * factor), int(g * factor), int(b * factor), a)

    @staticmethod
    def _px(img, x, y):
        """Safe pixel getter; returns transparent if out of bounds."""
        if 0 <= x < img.width and 0 <= y < img.height:
            return img.getpixel((x, y))
        return (0, 0, 0, 0)

    @staticmethod
    def _draw_3d_block(canvas, draw,
                       face_img,      # PIL image: the FRONT face pixels
                       side_img,      # PIL image: the RIGHT/LEFT side pixels
                       top_img,       # PIL image: the TOP face pixels
                       bx, by,        # canvas top-left of front face (px)
                       bw, bh,        # front face width & height (px)
                       depth=6,       # isometric depth (px)
                       shade_f=0.5):  # side darkening factor
        """
        Draw one rectangular block in isometric-ish 3-D on *canvas*.
        The depth goes upper-right (top face) and right (side face).
        """
        # ── front face ──────────────────────────────────────────
        if face_img:
            fi = face_img.resize((bw, bh), Image.Resampling.NEAREST)
            canvas.paste(fi, (bx, by), fi)

        # ── right side face (darkened) ───────────────────────────
        if side_img:
            si = side_img.resize((depth, bh), Image.Resampling.NEAREST)
            # darken every pixel
            sd = Image.new("RGBA", (depth, bh), (0, 0, 0, 0))
            for px in range(depth):
                for py in range(bh):
                    c = si.getpixel((px, py))
                    sd.putpixel((px, py), SkinManager._darken(c, shade_f))
            # skew: right edge goes up by depth pixels
            for px in range(depth):
                frac = px / (depth - 1) if depth > 1 else 0
                shift = int(frac * depth)            # top shrinks inward
                for py in range(bh):
                    c = sd.getpixel((px, py))
                    if c[3] > 0:
                        canvas.putpixel((bx + bw + px,
                                         by - shift + py), c)

        # ── top face (slightly darkened) ─────────────────────────
        if top_img:
            ti = top_img.resize((bw, depth), Image.Resampling.NEAREST)
            # apply gentle shading
            td = Image.new("RGBA", (bw, depth), (0, 0, 0, 0))
            for px in range(bw):
                for py in range(depth):
                    c = ti.getpixel((px, py))
                    td.putpixel((px, py), SkinManager._darken(c, 0.75))
            # skew: right edge goes up by depth pixels
            for px in range(bw):
                frac = px / (bw - 1) if bw > 1 else 0
                shift = int(frac * depth)
                for py in range(depth):
                    c = td.getpixel((px, py))
                    if c[3] > 0:
                        canvas.putpixel((bx + px,
                                         by - depth + shift + py), c)

    # ── public render method ──────────────────────────────────────
    @staticmethod
    def render_avatar(skin_path, cape_path, is_alex=False, view_back=False):
        # ── load skin ─────────────────────────────────────────────
        if skin_path and os.path.exists(skin_path):
            try:
                skin = Image.open(skin_path).convert("RGBA")
            except Exception:
                skin = SkinManager.get_default_steve()
        else:
            skin = SkinManager.get_default_steve()

        # ── load cape ─────────────────────────────────────────────
        cape = None
        if isinstance(cape_path, str) and cape_path.startswith("preset_"):
            cape = SkinManager.get_preset_cape(cape_path)
        elif cape_path and os.path.exists(str(cape_path)):
            try:
                cape = Image.open(cape_path).convert("RGBA")
            except Exception:
                cape = None

        # ── canvas: 160 × 320  (pixel-scale 8× before isometric extras) ──
        W, H   = 160, 320
        SCALE  = 8      # 1 skin-pixel → 8 canvas-pixels
        DEPTH  = 14     # isometric depth in canvas-pixels
        canvas = Image.new("RGBA", (W + DEPTH + 4, H + DEPTH + 4), (0, 0, 0, 0))
        draw   = ImageDraw.Draw(canvas)

        # pixel-scale: each MC block unit = SCALE px on canvas
        # Origin: leave top/left margin so top-face doesn't clip
        OX = 4   # canvas left margin
        OY = DEPTH + 4  # canvas top margin

        arm_w = 3 if is_alex else 4  # Alex slim arms

        def crop(x1, y1, x2, y2):
            """Crop from skin, guaranteed RGBA."""
            return skin.crop((x1, y1, x2, y2)).convert("RGBA")

        def block(face, side, top, bx, by, bw, bh):
            SkinManager._draw_3d_block(
                canvas, draw, face, side, top,
                OX + bx, OY + by, bw, bh, DEPTH)

        if not view_back:
            # ── FRONT VIEW ────────────────────────────────────────
            # HEAD  skin UV: face=8-16,8-16  right=0-8,8-16  top=8-16,0-8
            hf = crop(8, 8, 16, 16)
            hs = crop(0, 8, 8, 16)
            ht = crop(8, 0, 16, 8)
            if skin.height >= 64:
                hf = Image.alpha_composite(hf, crop(40, 8, 48, 16))
            block(hf, hs, ht,   bx=32, by=0,   bw=64, bh=64)

            # TORSO  face=20-28,20-32  right=16-20,20-32  top=20-28,16-20
            tf = crop(20, 20, 28, 32)
            ts = crop(16, 20, 20, 32)
            tt = crop(20, 16, 28, 20)
            if skin.height >= 64:
                tf = Image.alpha_composite(tf, crop(20, 36, 28, 48))
            block(tf, ts, tt,   bx=32, by=64,  bw=64, bh=96)

            # LEFT ARM  (facing us = right arm of Steve)
            la_w = arm_w
            laf = crop(44, 20, 44 + la_w, 32)
            las = crop(40, 20, 44, 32)
            lat = crop(44, 16, 44 + la_w, 20)
            block(laf, las, lat, bx=32 - la_w * SCALE, by=64, bw=la_w * SCALE, bh=96)

            # RIGHT ARM
            raf = crop(44, 20, 44 + la_w, 32)
            ras = crop(40, 20, 44, 32)
            rat = crop(44, 16, 44 + la_w, 20)
            block(raf, ras, rat, bx=96, by=64, bw=la_w * SCALE, bh=96)

            # LEFT LEG
            llf = crop(4, 20, 8, 32)
            lls = crop(0, 20, 4, 32)
            llt = crop(4, 16, 8, 20)
            block(llf, lls, llt, bx=32, by=160, bw=32, bh=96)

            # RIGHT LEG
            rlf = crop(4, 20, 8, 32)
            rls = crop(0, 20, 4, 32)
            rlt = crop(4, 16, 8, 20)
            block(rlf, rls, rlt, bx=64, by=160, bw=32, bh=96)

        else:
            # ── BACK VIEW ─────────────────────────────────────────
            hf = crop(24, 8, 32, 16)
            hs = crop(16, 8, 24, 16)
            ht = crop(24, 0, 32, 8)
            if skin.height >= 64:
                hf = Image.alpha_composite(hf, crop(56, 8, 64, 16))
            block(hf, hs, ht,   bx=32, by=0,   bw=64, bh=64)

            tbf = crop(32, 20, 40, 32)
            tbs = crop(28, 20, 32, 32)
            tbt = crop(32, 16, 40, 20)
            block(tbf, tbs, tbt, bx=32, by=64, bw=64, bh=96)

            lab = crop(52, 20, 56, 32)
            labb = crop(48, 20, 52, 32)
            labt = crop(52, 16, 56, 20)
            block(lab, labb, labt, bx=32 - la_w * SCALE if False else 8, by=64, bw=32, bh=96)

            rab = crop(52, 20, 56, 32)
            rabb = crop(48, 20, 52, 32)
            rabt = crop(52, 16, 56, 20)
            block(rab, rabb, rabt, bx=96, by=64, bw=32, bh=96)

            llb = crop(12, 20, 16, 32)
            llbb = crop(8, 20, 12, 32)
            llbt = crop(12, 16, 16, 20)
            block(llb, llbb, llbt, bx=32, by=160, bw=32, bh=96)

            rlb = crop(12, 20, 16, 32)
            rlbb = crop(8, 20, 12, 32)
            rlbt = crop(12, 16, 16, 20)
            block(rlb, rlbb, rlbt, bx=64, by=160, bw=32, bh=96)

            # Cape overlay on back
            if cape is not None:
                try:
                    cf = cape.crop((1, 1, 11, 17))
                    cf = cf.resize((64, 96), Image.Resampling.NEAREST)
                    # Slightly in front of body (offset -2 in Y = behind)
                    canvas.paste(cf, (OX + 32, OY + 60), cf)
                except Exception as e:
                    print(f"Cape paste error: {e}")

        # ── final scale to 160×320 ────────────────────────────────
        # Crop canvas tightly then resize
        final = canvas.crop((0, 0, W + DEPTH + 4, H + DEPTH + 4))
        final = final.resize((160, 320), Image.Resampling.LANCZOS)
        return SkinManager.pil_to_pixmap(final)

    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def render_skin_head(skin_path):
        if skin_path and os.path.exists(skin_path):
            try:
                skin = Image.open(skin_path).convert("RGBA")
                head = skin.crop((8, 8, 16, 16))
                if skin.height >= 64:
                    overlay = skin.crop((40, 8, 48, 16))
                    head = Image.alpha_composite(head, overlay)
                resized = head.resize((128, 128), Image.Resampling.NEAREST)
                return SkinManager.pil_to_pixmap(resized)
            except Exception:
                pass
        default_skin = SkinManager.get_default_steve()
        head = default_skin.crop((8, 8, 16, 16))
        resized = head.resize((128, 128), Image.Resampling.NEAREST)
        return SkinManager.pil_to_pixmap(resized)

    @staticmethod
    def pil_to_pixmap(pil_img):
        data  = pil_img.tobytes("raw", "RGBA")
        qimg  = QImage(data, pil_img.size[0], pil_img.size[1],
                       QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)
