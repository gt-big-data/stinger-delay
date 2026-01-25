from PIL import Image
import numpy as np

# --- CONFIG ---
INPUT = "/Users/fjansen/Downloads/Table&Tulip/T&T_Logos_Final/T&T_Monogram.png"
OUTPUT_PNG = "/Users/fjansen/Downloads/Table&Tulip/T&T_Logos_Final/favicon-tight-512.png"
OUTPUT_ICO = "/Users/fjansen/Downloads/Table&Tulip/T&T_Logos_Final/favicon-tight.ico"
TARGET_SIZE = 480        # favicon base size
PADDING = 0.08           # % of edge padding after cropping


# --- LOAD IMAGE ---
img = Image.open(INPUT).convert("RGBA")
arr = np.asarray(img)

# --- DETECT NON-WHITE / NON-EMPTY PIXELS ---
# Treat nearly-white or transparent as background
mask = ~(
        ((arr[...,0] > 245) & (arr[...,1] > 245) & (arr[...,2] > 245)) |
        (arr[...,3] < 10)
)

coords = np.argwhere(mask)

# If nothing detected, fallback
if coords.size == 0:
    cropped = img
else:
    y0, x0 = coords.min(axis=0)[:2]
    y1, x1 = coords.max(axis=0)[:2] + 1
    cropped = img.crop((x0, y0, x1, y1))


# --- ADD MINIMAL PADDING ---
cw, ch = cropped.size
pad = int(max(cw, ch) * PADDING)

square_size = max(cw, ch) + pad * 2

#canvas = Image.new("RGBA", (square_size, square_size), (0,0,0,0))
#canvas.paste(cropped, ((square_size - cw)//2, (square_size - ch)//2))
# *** White background version ***
canvas = Image.new("RGBA", (square_size, square_size), (255, 255, 255, 255))
canvas.paste(cropped, ((square_size - cw)//2, (square_size - ch)//2), cropped)

# --- RESIZE FOR FAVORICON ---
favicon = canvas.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)

# Save PNG
favicon.save(OUTPUT_PNG)

# Save ICO in multiple resolutions
favicon.save(
    OUTPUT_ICO,
    format="ICO",
    sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
)

OUTPUT_PNG, OUTPUT_ICO
