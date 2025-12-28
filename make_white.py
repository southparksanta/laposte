from PIL import Image

def make_white():
    pt = 'c:/Users/hanih/Documents/laPoste/static/img/logo.png'
    img = Image.open(pt)
    img = img.convert("RGBA")
    datas = img.getdata()

    newData = []
    for item in datas:
        # If alpha is 0 (transparent), keep it transparent
        if item[3] == 0:
            newData.append(item)
        else:
            # Otherwise make it white, keeping the alpha channel if it's not fully opaque (for antialiasing)
            # Or just hard set to white. Let's maintain alpha.
            newData.append((255, 255, 255, item[3]))

    img.putdata(newData)
    img.save(pt, "PNG")
    print("Saved white logo to", pt)

if __name__ == '__main__':
    make_white()
