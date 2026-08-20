import random
from functools import partial
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch import nn
from torch.utils.data import Dataset
from torchvision import transforms as T

from .utils import convert_image_to_fn, exists
from .graph_encoder import collate, get_nodes, get_dgl

# dataset classes
def image2tensor(img:Image.Image):
    img_array=np.array(img)/17
    img_tensor=torch.tensor(img_array,dtype=torch.float32).unsqueeze(0)
    return img_tensor

def image2multitensor(img: Image.Image):
    img_array = np.array(img)
    multitensors = (img_array[..., None] == np.arange(18)).astype(np.float32)
    final_tensor = torch.tensor(multitensors, dtype=torch.float32).permute(2, 0, 1)
    return final_tensor

class Dataset(Dataset):
    def __init__(
        self,
        folder_image,
        folder_mask,
        folder_text,
        image_size,
        exts=["jpg", "jpeg", "png", "tiff"],
        augment_flip=False,
        augment_affine=False,
        convert_image_to=None,
        mask=0,
        onehot=True
    ):
        super().__init__()
        # self.folder = folder
        self.image_size = image_size
        self.augment_flip = augment_flip
        self.augment_affine = augment_affine
        self.mask = mask
        self.onehot=onehot
        self.image_paths = [
            p for ext in exts for p in Path(f"{folder_image}").glob(f"**/*.{ext}")
        ]
        self.mask_paths = [
            p for ext in exts for p in Path(f"{folder_mask}").glob(f"**/*.{ext}")
        ]
        self.image_paths.sort(key=lambda x: int(x.stem.split("_")[0]))
        self.mask_paths.sort(key=lambda x: int(x.stem.split("_")[0]))
        self.text_path = next(Path(f"{folder_text}").glob(f"**/*.csv"))
        texts = pd.read_csv(self.text_path)
        self.texts = [p for p in zip(texts["0"], texts["1"])]
        self.texts.sort(
            key=lambda x: int(
                x[0].replace(".png", "").replace(".json", "").split("/")[-1]
            )
        )
        assert (
            len(self.image_paths) == len(self.mask_paths) == len(self.texts)
        ), "number of images, masks and texts should be the same"
        maybe_convert_fn = (
            partial(convert_image_to_fn, convert_image_to)
            if exists(convert_image_to)
            else nn.Identity()
        )

        self.transform = T.Compose(
            [
                T.Lambda(maybe_convert_fn),
                T.Resize(image_size),
                T.CenterCrop(image_size),
                # T.ToTensor(),
            ]
        )

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, index):
        image_path = self.image_paths[index]
        mask_path = self.mask_paths[index]
        img = Image.open(image_path)
        mask = Image.open(mask_path)
        img = self.transform(img)
        if self.onehot:
            img=image2multitensor(img)
        else:
            img = image2tensor(img)
        mask = self.transform(mask)
        mask = T.ToTensor()(mask)
        if self.augment_affine:
            a=torch.stack([img,mask])
            a=T.RandomAffine(degrees=0, translate=(0.25,0.25))(a)
            img,mask=a[0],a[1]
        if self.augment_flip and random.random() > 0.5:
            img = T.RandomHorizontalFlip(p=1)(img)
            mask = T.RandomHorizontalFlip(p=1)(mask)
        if self.augment_flip and random.random() > 0.5:
            img = T.RandomVerticalFlip(p=1)(img)
            mask = T.RandomVerticalFlip(p=1)(mask)
        text = self.texts[index][1]
        nodes = get_nodes(text)
        graph = get_dgl(nodes, mask=self.mask)
        return img, mask, text, graph, image_path.stem


def collate_fn(data):
    img = torch.stack([i[0] for i in data])
    mask = torch.stack([i[1] for i in data])
    text = [i[2] for i in data]
    graphs = [i[3] for i in data]
    attn_mask, node_feat, in_degree, out_degree, path_data, dist = collate(graphs)
    image_path_stem = [i[4] for i in data]
    graphormer_dict = {
        "attn_mask": attn_mask,
        "node_feat": node_feat,
        "in_degree": in_degree,
        "out_degree": out_degree,
        "path_data": path_data,
        "dist": dist,
    }
    return img, mask, text, graphormer_dict, image_path_stem
