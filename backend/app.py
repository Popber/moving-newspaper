import os
import uuid
import subprocess
import tempfile
from pathlib import Path

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)
CORS(app)

CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "fhbtcmuv")
UPLOAD_PRESET = os.environ.get("CLOUDINARY_UPLOAD_PRESET", "moving_newspaper")

W, H = 700, 1000
# Slightly smaller and more centered photo area so the moving image sits neatly inside the frame
PHOTO_BOX = (245, 395, 455, 555)

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def kfont(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/nanum/NanumMyeongjoBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return font(size, bold)

F_SMALL = font(16)
F_BODY = font(17)
F_BODY_B = font(18, True)
F_HEAD = font(38, True)
F_MAST = font(50, True)
F_CAP = font(15)
F_STAMP = font(20, True)

KF_HEAD_BIG = kfont(62, True)
KF_SUB = kfont(22, True)

def draw_wrapped(draw, text, xy, width_px, font_obj, fill, line_gap=4, max_lines=8):
    x, y = xy
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textlength(test, font=font_obj) <= width_px:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
            if len(lines) >= max_lines:
                break
    if line and len(lines) < max_lines:
        lines.append(line)
    bbox = draw.textbbox((0, 0), "Ag", font=font_obj)
    lh = bbox[3] - bbox[1] + line_gap
    for ln in lines:
        draw.text((x, y), ln, font=font_obj, fill=fill)
        y += lh
    return y

def parchment():
    img = Image.new("RGB", (W, H), "#d6b77e")
    px = img.load()
    import random
    rnd = random.Random(42)
    for y in range(H):
        for x in range(W):
            edge = min(x, y, W - 1 - x, H - 1 - y)
            vign = int(max(0, 35 - edge))
            noise = rnd.randint(-7, 7)
            r = int(max(0, min(255, 222 + noise - vign)))
            g = int(max(0, min(255, 195 + noise - vign)))
            b = int(max(0, min(255, 137 + noise - vign)))
            px[x, y] = (r, g, b)
    return img.filter(ImageFilter.GaussianBlur(0.18))

def cover(im, size):
    tw, th = size
    iw, ih = im.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))

def static_newspaper(name=""):
    img = parchment()
    d = ImageDraw.Draw(img)
    ink = "#2b1e13"

    # Masthead
    d.text((W // 2, 38), "THE YOUTH PROPHET", font=F_MAST, fill=ink, anchor="ma")
    d.line((40, 95, W - 40, 95), fill=ink, width=2)
    d.line((40, 102, W - 40, 102), fill=ink, width=1)
    d.text((44, 114), "MAGICAL NEWS • FESTIVAL SPECIAL EDITION", font=F_SMALL, fill=ink)
    d.text((W - 44, 114), "OCTOBER 17, 2026", font=F_SMALL, fill=ink, anchor="ra")
    d.line((40, 140, W - 40, 140), fill=ink, width=1)

    # Single-line main headline + subtitle
    # Stronger single-line festival headline
    d.text(
        (W // 2, 205),
        "즐거움만수두룩",
        font=KF_HEAD_BIG,
        fill=ink,
        anchor="ma",
        stroke_width=1,
        stroke_fill=ink
    )
    d.text((W // 2, 275), "수리산 마법학교", font=KF_SUB, fill=ink, anchor="ma")
    d.line((150, 292, 550, 292), fill=ink, width=1)
    d.line((40, 315, W - 40, 315), fill=ink, width=1)

    # Side columns
    d.text((45, 340), "Mysterious News", font=F_BODY_B, fill=ink)
    d.line((45, 367, 195, 367), fill=ink, width=1)
    left = (
        "A remarkable figure appeared at the Surisan festival, drawing visitors "
        "into an atmosphere of magic, performance and imagination. Witnesses "
        "said the living portrait looked as if it had stepped straight out of an old newspaper."
    )
    draw_wrapped(d, left, (45, 380), 145, F_BODY, ink, 3, 9)

    d.text((505, 340), "Daily Magic", font=F_BODY_B, fill=ink)
    d.line((505, 367, 655, 367), fill=ink, width=1)
    right = (
        "Editors requested a lively pose worthy of a magical special issue. "
        "Every gesture added charm to the moving portrait and gave the page "
        "the feeling of an enchanted bulletin."
    )
    draw_wrapped(d, right, (505, 380), 145, F_BODY, ink, 3, 9)

    # Photo frame
    x1, y1, x2, y2 = PHOTO_BOX
    d.rectangle((x1 - 6, y1 - 6, x2 + 6, y2 + 6), fill="#2f241b", outline="#4a3422", width=3)

    # Caption
    cap = f"{name} — Featured wizard at Surisan Magic School." if name else "Featured wizard at Surisan Magic School."
    d.text((W // 2, 575), cap, font=F_CAP, fill=ink, anchor="ma")

    # Bottom articles
    d.line((40, 610, W - 40, 610), fill=ink, width=1)
    d.text((45, 625), "Breaking Story", font=F_HEAD, fill=ink)
    center = (
        "This special moving newspaper preserves a short festival moment as a looping image. "
        "The vintage page combines old paper texture, classic editorial columns and a custom festival headline "
        "to create a one-of-a-kind magical souvenir."
    )
    draw_wrapped(d, center, (45, 678), 610, F_BODY, ink, 5, 7)

    d.line((40, 825, W - 40, 825), fill=ink, width=1)
    d.text((45, 842), "Festival Watch", font=F_BODY_B, fill=ink)
    draw_wrapped(
        d,
        "The appearance quickly became one of the most talked-about moments of the day.",
        (45, 874), 275, F_BODY, ink, 4, 5
    )
    d.text((365, 842), "Exclusive", font=F_BODY_B, fill=ink)
    draw_wrapped(
        d,
        "This edition was generated for one participant and can be opened directly by QR.",
        (365, 874), 285, F_BODY, ink, 4, 5
    )

    stamp = Image.new("RGBA", (190, 55), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.rectangle((2, 2, 188, 53), outline=(120, 35, 25, 190), width=3)
    sd.text((95, 27), "MOVING EDITION", font=F_STAMP, fill=(120, 35, 25, 210), anchor="mm")
    stamp = stamp.rotate(7, expand=True, resample=Image.Resampling.BICUBIC)
    img.paste(stamp, (470, 920), stamp)
    return img

def extract_frames(video_path, frame_dir):
    pattern = str(frame_dir / "frame_%02d.png")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=6.7,scale=320:240:force_original_aspect_ratio=increase,crop=320:240",
        "-frames:v", "8", pattern
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    frames = sorted(frame_dir.glob("frame_*.png"))
    if not frames:
        raise RuntimeError("영상 프레임을 추출하지 못했습니다.")
    while len(frames) < 8:
        frames.append(frames[-1])
    return frames[:8]

def compose_gif(frame_files, output_path, name):
    base = static_newspaper(name)
    x1, y1, x2, y2 = PHOTO_BOX
    target = (x2 - x1, y2 - y1)
    pages = []
    for fp in frame_files:
        portrait = Image.open(fp).convert("RGB")
        portrait = cover(portrait, target)
        page = base.copy()
        page.paste(portrait, (x1, y1))
        pages.append(page.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))
    pages[0].save(
        output_path,
        save_all=True,
        append_images=pages[1:],
        duration=150,
        loop=0,
        disposal=2,
        optimize=False
    )

def cloudinary_upload(gif_path):
    endpoint = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload"
    with open(gif_path, "rb") as f:
        files = {"file": ("moving-newspaper.gif", f, "image/gif")}
        data = {"upload_preset": UPLOAD_PRESET}
        r = requests.post(endpoint, files=files, data=data, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Cloudinary upload failed: {r.text}")
    data = r.json()
    secure = data["secure_url"]
    download = secure.replace("/upload/", "/upload/fl_attachment/")
    return secure, download

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "version": "text-title-v5",
        "headline": "즐거움만수두룩 / 수리산 마법학교 (layout v5)",
        "photo_box": PHOTO_BOX
    })

@app.post("/generate")
def generate():
    if "video" not in request.files:
        return jsonify({"error": "video 파일이 없습니다."}), 400

    name = (request.form.get("name") or "").strip()[:30]
    uid = uuid.uuid4().hex[:10]

    try:
        with tempfile.TemporaryDirectory(prefix="movingnews_") as td:
            td = Path(td)
            src = td / f"{uid}.webm"
            request.files["video"].save(src)

            frames_dir = td / "frames"
            frames_dir.mkdir()
            frames = extract_frames(src, frames_dir)

            out = td / f"{uid}.gif"
            compose_gif(frames, out, name)
            gif_url, download_url = cloudinary_upload(out)

        return jsonify({"ok": True, "gif_url": gif_url, "download_url": download_url})
    except subprocess.CalledProcessError as e:
        msg = e.stderr.decode("utf-8", "ignore")[-1500:] if e.stderr else str(e)
        return jsonify({"error": "FFmpeg 처리 실패", "detail": msg}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
