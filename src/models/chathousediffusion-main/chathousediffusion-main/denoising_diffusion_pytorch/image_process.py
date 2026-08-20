import numpy as np
from PIL import Image
import torch

room_label = [
    (0, "LivingRoom", 1, "PublicArea", [220, 213, 205]),
    (1, "MasterRoom", 0, "Bedroom", [138, 113, 91]),
    (2, "Kitchen", 1, "FunctionArea", [244, 245, 247]),
    (3, "Bathroom", 0, "FunctionArea", [224, 225, 227]),
    (4, "DiningRoom", 1, "FunctionArea", [200, 193, 185]),
    (5, "ChildRoom", 0, "Bedroom", [198, 173, 151]),
    (6, "StudyRoom", 0, "Bedroom", [178, 153, 131]),
    (7, "SecondRoom", 0, "Bedroom", [158, 133, 111]),
    (8, "GuestRoom", 0, "Bedroom", [189, 172, 146]),
    (9, "Balcony", 1, "PublicArea", [244, 237, 224]),
    (10, "Entrance", 1, "PublicArea", [238, 235, 230]),
    (11, "Storage", 0, "PublicArea", [226, 220, 206]),
    (12, "Wall-in", 0, "PublicArea", [226, 220, 206]),
    (13, "External", 0, "External", [255, 255, 255]),
    (14, "ExteriorWall", 0, "ExteriorWall", [0, 0, 0]),
    (15, "FrontDoor", 0, "FrontDoor", [255, 255, 0]),
    (16, "InteriorWall", 0, "InteriorWall", [128, 128, 128]),
    (17, "InteriorDoor", 0, "InteriorDoor", [255, 255, 255]),
]

# def get_color_map():
#     color = np.array([
#         [244,242,229], # living room
#         [253,244,171], # bedroom
#         [234,216,214], # kitchen
#         [205,233,252], # bathroom
#         [208,216,135], # balcony
#         [249,222,189], # Storage
#         [ 79, 79, 79], # exterior wall
#         [255,225, 25], # FrontDoor
#         [128,128,128], # interior wall
#         [255,255,255]
#     ],dtype=np.int64)
#     cIdx  = np.array([1,2,3,4,1,2,2,2,2,5,1,6,1,10,7,8,9,10])-1
#     return color[cIdx]
# cmap = get_color_map()/255.0


def get_color_map():
    color = np.array(
        [
            [238, 232, 170],  # living room 1
            [255, 165, 0],  # Master room 2
            [240, 128, 128],  # kitchen 3
            [173, 216, 210],  # bathroom 4
            [107, 142, 35],  # balcony 5
            [218, 112, 214],  # dinning room 6
            [221, 160, 221],  # Storage 7
            [255, 215, 0],  # Common room 8
            [0, 0, 0],  # exterior wall 9
            [255, 225, 25],  # FrontDoor 10
            [128, 128, 128],  # interior wall 11
            [255, 255, 255],
        ],
        dtype=np.int64,
    )
    cIdx = np.array([1, 2, 3, 4, 6, 8, 8, 8, 8, 5, 1, 7, 1, 12, 9, 10, 12, 12]) - 1
    return color[cIdx]


cmap = get_color_map() / 255.0


def convert_gray_to_rgb(img):
    img = img.mul(17).permute(1, 2, 0)
    img = torch.round(img).to(dtype=torch.int)
    rgb = torch.zeros((img.shape[0], img.shape[1], 3), device=img.device)
    for i in range(18):
        rgb = torch.where(
            img == i,
            torch.tensor(cmap[i], device=img.device).unsqueeze(0).unsqueeze(0),
            rgb,
        )
    return rgb.permute(2, 0, 1)


def convert_mult_to_rgb(img, feature):
    img = torch.argmax(img, dim=0)
    rgb = torch.zeros((img.shape[0], img.shape[1], 3), device=img.device)
    for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17]:
        rgb = torch.where(
            img.unsqueeze(-1) == i,
            torch.tensor(cmap[i], device=img.device).unsqueeze(0).unsqueeze(0),
            rgb,
        )
    rgb = torch.where(
        torch.round(feature.permute(1, 2, 0)) == 1,
        torch.tensor(cmap[13], device=img.device).unsqueeze(0).unsqueeze(0),
        rgb,
    )
    return rgb.permute(2, 0, 1)


def load_image(path):
    img = Image.open(path)
    img = np.array(img)
    rgb = convert_gray_to_rgb(img)
    rgb = Image.fromarray(rgb)
    rgb.save("0_rgb.png")
    return img


# load_image("data/dataset/output64/0.png")
if __name__ == "__main__":
    img = torch.randint(0, 2, (18, 64, 64))
    convert_mult_to_rgb(img)
