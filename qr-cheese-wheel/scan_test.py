#!/usr/bin/env python3
"""
How small can the QR modules be?  A simulated scan test.

    python3 scan_test.py ["https://your-link"]

For each module size it draws the code as printed, roughs it up the way an FDM
print and a phone camera would, and tries to decode it with two independent
decoders (ZXing, the library behind many Android scanners, and OpenCV's).
For each module size it prints the share of trials that decoded.

What a trial simulates (all of it random within the ranges below):
  print    dark modules spread or shrink by up to 0.15 mm (over/under-extrusion),
           each module edge wanders by up to 0.08 mm, corners round off
  relief   the modules stand QR_HEIGHT proud, so a tilted camera also sees
           their dark side walls: the dark grows by h*tan(tilt) on one side
  camera   tilted up to 35 degrees, 3 to 7 pixels per mm (roughly a phone held
           45 cm to 20 cm away, scanning a 1080p preview), defocus blur,
           sensor noise, JPEG compression
  light    a brightness gradient, plus the shadow of the notch wall falling
           across part of the code

It is a model, not a phone: use it to compare sizes, then confirm with a test
print of the tile, which takes about 20 minutes.
"""
import sys
import numpy as np, cv2, qrcode, zxingcpp

QR_HEIGHT = 0.48
QUIET = 3
PX_MM = 24                       # resolution of the "printed" master image
YELLOW, DARK = 200, 40           # grey levels of matte yellow and dark brown PLA under room light

def master(M, m, rng):
    n = M.shape[0]
    size = int((n + 2 * QUIET) * m * PX_MM)
    img = np.full((size, size), 255, np.uint8)
    bleed = rng.uniform(-0.10, 0.15) * PX_MM
    jit = 0.08 * PX_MM
    off = QUIET * m * PX_MM
    for i in range(n):
        for j in range(n):
            if M[i, j]:
                x0 = off + j * m * PX_MM - bleed + rng.uniform(-jit, jit)
                x1 = off + (j + 1) * m * PX_MM + bleed + rng.uniform(-jit, jit)
                y0 = off + i * m * PX_MM - bleed + rng.uniform(-jit, jit)
                y1 = off + (i + 1) * m * PX_MM + bleed + rng.uniform(-jit, jit)
                cv2.rectangle(img, (int(x0), int(y0)), (int(x1), int(y1)), 0, -1)
    img = cv2.GaussianBlur(img, (0, 0), 0.12 * PX_MM)          # rounded corners and edges
    return (img > 127).astype(np.float32)                       # 1 = light, 0 = dark

def shoot(light, m, rng):
    h, w = light.shape
    tilt = np.radians(rng.uniform(0, 35))
    az = rng.uniform(0, 2 * np.pi)
    # side walls of the raised modules: shift the dark toward the camera by h*tan(tilt)
    shift = QR_HEIGHT * np.tan(tilt) * PX_MM
    dx, dy = shift * np.cos(az), shift * np.sin(az)
    moved = cv2.warpAffine(light, np.float32([[1, 0, dx], [0, 1, dy]]), (w, h), borderValue=1)
    light = np.minimum(light, moved)
    # lighting: gradient and a wall shadow across one side
    yy, xx = np.mgrid[0:h, 0:w] / max(h, w)
    g = 1 - 0.25 * rng.uniform() * (np.cos(az) * xx + np.sin(az) * yy)
    edge = rng.uniform(0.15, 0.45)
    shadow = np.where(xx < edge, rng.uniform(0.55, 0.8), 1.0) if rng.uniform() < 0.7 else 1.0
    grey = (DARK + (YELLOW - DARK) * light) * g * shadow
    # pad with background (yellow tile, beyond it the wheel) and look at it at an angle
    pad = int(15 * PX_MM)
    grey = cv2.copyMakeBorder(grey.astype(np.float32), pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=YELLOW * 0.9)
    H, W = grey.shape
    ppm = rng.uniform(3, 7)                                    # camera pixels per mm
    s = ppm / PX_MM
    k = np.sin(tilt) * 0.35                                    # perspective strength
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    c = np.cos(tilt)
    dst = np.float32([[0, 0], [W, 0], [W * (1 - k / 2), H * c], [W * k / 2, H * c]])
    rot = cv2.getRotationMatrix2D((W / 2, H / 2), np.degrees(az), 1)
    grey = cv2.warpAffine(grey, rot, (W, H), borderValue=YELLOW * 0.9)
    P = cv2.getPerspectiveTransform(src, dst * s)
    out = cv2.warpPerspective(grey, P, (int(W * s) + 2, int(H * s) + 2), flags=cv2.INTER_AREA, borderValue=YELLOW * 0.9)
    out = cv2.GaussianBlur(out, (0, 0), rng.uniform(0.4, 1.1))     # focus
    out = out + rng.normal(0, 4, out.shape)                        # sensor noise
    out = np.clip(out, 0, 255).astype(np.uint8)
    ok, jpg = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return cv2.imdecode(jpg, cv2.IMREAD_GRAYSCALE)

def decodes(img, url):
    z = any(r.text == url for r in zxingcpp.read_barcodes(img))
    o = cv2.QRCodeDetector().detectAndDecode(img)[0] == url
    return z, o

def run(url, sizes, trials=60, seed=1):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    q.add_data(url); q.make(fit=True)
    M = np.array(q.get_matrix(), bool)
    print(f"{M.shape[0]}x{M.shape[0]} code, ECC M, {trials} trials per size")
    print(" module   code     ZXing   OpenCV   either")
    for m in sizes:
        rng = np.random.default_rng(seed)
        zs = os_ = es = 0
        for _ in range(trials):
            z, o = decodes(shoot(master(M, m, rng), m, rng), url)
            zs += z; os_ += o; es += z or o
        print(f" {m:.2f} mm {M.shape[0] * m:5.1f} mm  {100 * zs / trials:4.0f}%   {100 * os_ / trials:4.0f}%    {100 * es / trials:4.0f}%")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.olympiaprovisions.com/gift_cards/1234567/0123456789abcdef0123456789abcdef"
    run(url, [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5])
