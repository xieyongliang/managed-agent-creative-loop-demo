"""Places sample artwork on the blank mug of an archived mockup photo. Images travel as BMP through sips."""
import os, struct, subprocess, sys, tempfile
import numpy as np

SCRATCH = tempfile.mkdtemp()

def read(path):
    bmp = os.path.join(SCRATCH, os.path.basename(path) + ".bmp")
    subprocess.run(["sips", "-s", "format", "bmp", path, "--out", bmp], check=True, capture_output=True)
    raw = open(bmp, "rb").read()
    offset, = struct.unpack("<I", raw[10:14])
    width, height, _, bpp = struct.unpack("<iiHH", raw[18:30])
    step = bpp // 8
    row = (width * step + 3) // 4 * 4
    rows = np.frombuffer(raw, dtype=np.uint8, count=row * abs(height), offset=offset).reshape(abs(height), row)[:, :width * step]
    image = rows.reshape(abs(height), width, step)[:, :, :3][:, :, ::-1]
    return (image[::-1] if height > 0 else image).astype(np.float32)

def write(image, path, quality=88):
    h, w, _ = image.shape
    data = np.clip(image, 0, 255).astype(np.uint8)[::-1, :, ::-1]
    pad = (4 - w * 3 % 4) % 4
    body = b"".join(r.tobytes() + b"\0" * pad for r in data)
    head = b"BM" + struct.pack("<IHHI", 54 + len(body), 0, 0, 54) + struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(body), 2835, 2835, 0, 0)
    bmp = os.path.join(SCRATCH, "out.bmp")
    open(bmp, "wb").write(head + body)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality), bmp, "--out", path], check=True, capture_output=True)

def resize(image, size):
    h, w, _ = image.shape
    ys = (np.arange(size) + .5) * h / size - .5
    xs = (np.arange(size) + .5) * w / size - .5
    # area-ish sampling: average a small neighbourhood to avoid aliasing when shrinking
    out = np.zeros((size, size, 3), np.float32)
    taps = max(1, int(round(h / size)))
    for dy in range(taps):
        for dx in range(taps):
            yy = np.clip(np.round(ys + dy - taps / 2 + .5).astype(int), 0, h - 1)
            xx = np.clip(np.round(xs + dx - taps / 2 + .5).astype(int), 0, w - 1)
            out += image[yy][:, xx]
    return out / (taps * taps)

mug = read(sys.argv[1])
art = read(sys.argv[2])
H, W, _ = mug.shape
k = W / 2048
# 1. remove the existing print: blend each column between the clean rows above and below it
x0, x1, y0, y1 = int(680 * k), int(1300 * k), int(1040 * k), int(1340 * k)
top, bottom = mug[y0 - 6:y0].mean(axis=0), mug[y1:y1 + 6].mean(axis=0)
t = np.linspace(0, 1, y1 - y0)[:, None, None]
patch = top[None, x0:x1] * (1 - t) + bottom[None, x0:x1] * t
rng = np.random.default_rng(3)
mug[y0:y1, x0:x1] = patch + rng.normal(0, .8, patch.shape)
# 2. wrap the artwork around the cylinder and multiply it into the glaze
cx, cy, radius, arc = 992 * k, 1150 * k, 372 * k, int(float(sys.argv[4] if len(sys.argv) > 4 else 620) * k)
art = resize(art, arc)
half = radius * np.sin(arc / 2 / radius)
for px in range(int(cx - half), int(cx + half)):
    u = radius * np.arcsin((px - cx) / radius) + arc / 2
    lo = int(np.clip(np.floor(u), 0, arc - 1)); hi = min(lo + 1, arc - 1); f = u - np.floor(u)
    column = art[:, lo] * (1 - f) + art[:, hi] * f
    ys = slice(int(cy - arc / 2), int(cy - arc / 2) + arc)
    ink = column / 255.0
    mug[ys, px] = mug[ys, px] * (ink * .96 + .04 * ink ** 2)
write(mug, sys.argv[3])
print("ok", mug.shape)
