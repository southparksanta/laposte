from PIL import Image

def make_transparent():
    pt = 'c:/Users/hanih/Documents/laPoste/static/img/logo.png'
    img = Image.open(pt)
    img = img.convert("RGBA")
    datas = img.getdata()

    newData = []
    for item in datas:
        # Check if pixel is white-ish (background)
        # item is (R, G, B, A)
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(pt, "PNG")
    print("Saved transparent logo to", pt)

if __name__ == '__main__':
    make_transparent()
