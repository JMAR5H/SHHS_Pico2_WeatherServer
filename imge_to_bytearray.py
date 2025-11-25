from PIL import Image

def png_to_bytearray(path):
    """
    Convert a monochrome PNG of any size into a bytearray
    suitable for SSD1306 128x64 (1 bit per pixel, MONO_VLSB).
    """
    W, H = 128, 64

    # Open and convert to 1-bit (monochrome)
    img = Image.open(path).convert("1")

    # Resize to 128x64 (fit to display)
    img = img.resize((W, H), Image.ANTIALIAS)

    # Prepare bytearray (1 bit per pixel, vertical LSB format)
    buf = bytearray(W * H // 8)

    pixels = img.load()
    for y in range(H):
        for x in range(W):
            if pixels[x, y] == 0:  # black pixel = ON
                buf[x + (y // 8) * W] |= (1 << (y % 8))

    return buf


# Example usage:
buf = png_to_bytearray("eye6.png")
print(len(buf))   # should be 1024 bytes
print(buf)
