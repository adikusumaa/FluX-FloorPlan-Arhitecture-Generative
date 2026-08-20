from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader

from torch.optim import Adam

from torchvision import utils

from tqdm.auto import tqdm
from ema_pytorch import EMA


from .version import __version__

import os

from .utils import exists, has_int_squareroot, divisible_by, convert_image_to_fn, seed_torch
from .dataset import Dataset, collate_fn
from .eval import cal_iou
from itertools import cycle
from .image_process import convert_gray_to_rgb, convert_mult_to_rgb
from .graph_encoder import get_nodes, get_dgl, collate, MAX_NUM_NODES
from .cross_attention_edit import AttentionEdit

from torchvision import transforms as T
from functools import partial
from PIL import Image


# trainer class


class Trainer(object):
    def __init__(
        self,
        diffusion_model,
        folder_image,
        folder_mask,
        folder_text,
        *,
        train_batch_size=16,
        gradient_accumulate_every=1,
        augment_flip=True,
        train_lr=1e-4,
        train_num_steps=100000,
        ema_update_every=10,
        ema_decay=0.995,
        adam_betas=(0.9, 0.99),
        save_and_sample_every=1000,
        num_samples=25,
        results_folder="./results",
        convert_image_to=None,
        max_grad_norm=1.0,
        cond_scale=1,
        mask=0.1,
        use_graphormer=True,
        onehot=True,
        train_num_workers=8,
        mode="train",
        inject_step=25,
    ):
        super().__init__()

        # model

        self.model = diffusion_model
        self.channels = diffusion_model.channels
        self.onehot = onehot

        # default convert_image_to depending on channels

        if not exists(convert_image_to):
            convert_image_to = {1: "L", 3: "RGB", 4: "RGBA"}.get(3)

        # sampling and training hyperparameters

        assert has_int_squareroot(
            num_samples
        ), "number of samples must have an integer square root"
        self.num_samples = num_samples
        self.save_and_sample_every = save_and_sample_every

        self.batch_size = train_batch_size
        self.gradient_accumulate_every = gradient_accumulate_every
        assert (
            train_batch_size * gradient_accumulate_every
        ) >= 16, f"your effective batch size (train_batch_size x gradient_accumulate_every) should be at least 16 or above"

        self.train_num_steps = train_num_steps
        self.image_size = diffusion_model.image_size

        self.max_grad_norm = max_grad_norm

        # dataset and dataloader
        if mode == "train":
            self.train_ds = Dataset(
                folder_image,
                folder_mask,
                folder_text,
                self.image_size,
                augment_flip=augment_flip,
                augment_affine=True,
                convert_image_to=convert_image_to,
                mask=mask,
                onehot=onehot,
            )
            assert (
                len(self.train_ds) >= 100
            ), "you should have at least 100 images in your folder. at least 10k images recommended"
            train_dl = DataLoader(
                self.train_ds,
                batch_size=train_batch_size,
                shuffle=True,
                pin_memory=False,
                # num_workers=8,
                num_workers=train_num_workers,
                collate_fn=collate_fn,
            )
            self.train_dl = cycle(train_dl)

        if mode == "train" or mode == "val":
            self.val_ds = Dataset(
                folder_image + "_test",
                folder_mask + "_test",
                folder_text + "_test",
                self.image_size,
                augment_flip=augment_flip,
                augment_affine=False,
                convert_image_to=convert_image_to,
                mask=0,
                onehot=onehot,
            )

            val_dl = DataLoader(
                self.val_ds,
                batch_size=train_batch_size,
                shuffle=False,
                pin_memory=False,
                num_workers=0,
                collate_fn=collate_fn,
            )

            self.val_dl = val_dl

        if mode == "predict":
            self.cross_attention_edit = AttentionEdit(
                total_steps=self.model.sampling_timesteps, inject_step=inject_step
            )
            self.model.cross_attention_edit = self.cross_attention_edit
            self.model.model.cross_attention_edit = self.cross_attention_edit

        # optimizer

        self.opt = Adam(diffusion_model.parameters(), lr=train_lr, betas=adam_betas)

        # for logging results in a folder periodically

        self.ema = EMA(diffusion_model, beta=ema_decay, update_every=ema_update_every)
        self.ema.to(self.device)

        self.results_folder = Path(results_folder)
        self.results_folder.mkdir(exist_ok=True)

        # step counter state

        self.step = 0
        self.cond_scale = cond_scale
        self.use_graphormer = use_graphormer

    @property
    def device(self):
        return "cuda"

    def save(self, milestone):

        data = {
            "step": self.step,
            "model": self.model.state_dict(),
            "opt": self.opt.state_dict(),
            "ema": self.ema.state_dict(),
            "scaler": (None),
            "version": __version__,
        }

        torch.save(data, str(self.results_folder / f"model-{milestone}.pt"))

    def load(self, milestone):
        device = self.device

        data = torch.load(
            str(self.results_folder / f"model-{milestone}.pt"), map_location=device
        )

        model = self.model
        data["model"]["model.graph_drop_embedded"] = data["model"][
            "model.graph_drop_embedded"
        ][:, :MAX_NUM_NODES, :]
        data["ema"]["ema_model.model.graph_drop_embedded"] = data["ema"][
            "ema_model.model.graph_drop_embedded"
        ][:, :MAX_NUM_NODES, :]
        data["ema"]["online_model.model.graph_drop_embedded"] = data["ema"][
            "online_model.model.graph_drop_embedded"
        ][:, :MAX_NUM_NODES, :]
        model.load_state_dict(data["model"])

        self.step = data["step"]
        self.opt.load_state_dict(data["opt"])
        self.ema.load_state_dict(data["ema"])

        if "version" in data:
            print(f"loading from version {data['version']}")

    def train(self):

        with tqdm(
            initial=self.step,
            total=self.train_num_steps,
            position=0,
        ) as pbar:

            while self.step < self.train_num_steps:
                # profiler = Profiler()
                # profiler.start()
                total_loss = 0.0

                for _ in range(self.gradient_accumulate_every):
                    img, feature, text, graphormer_dict, _ = next(self.train_dl)
                    img = img.to(self.device)
                    feature = feature.to(self.device)
                    graphormer_dict = {
                        k: v.to(self.device) for k, v in graphormer_dict.items()
                    }

                    if self.use_graphormer:
                        text = None
                    else:
                        graphormer_dict = None
                    loss = self.model(img, feature, text, graphormer_dict)
                    loss = loss / self.gradient_accumulate_every
                    total_loss += loss.item()

                    loss.backward()

                pbar.set_description(f"loss: {total_loss:.4f}")

                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), self.max_grad_norm
                )

                self.opt.step()
                self.opt.zero_grad()
                self.step += 1
                self.ema.update()

                if self.step != 0 and divisible_by(
                    self.step, self.save_and_sample_every
                ):
                    self.ema.ema_model.eval()
                    milestone = self.step // self.save_and_sample_every
                    self.val(milestone=milestone)
                    self.save(milestone)
                    torch.cuda.empty_cache()
                pbar.update(1)

    def val(self, milestone=None, load_model=None):
        if milestone is not None:
            if not os.path.exists(self.results_folder / f"step-{milestone}"):
                os.makedirs(self.results_folder / f"step-{milestone}")
            filepath = f"step-{milestone}"
        elif load_model is not None:
            self.load(load_model)
            self.ema.copy_params_from_model_to_ema()
            self.ema.ema_model.eval()
            if not os.path.exists(
                self.results_folder / f"cond_scale-{self.cond_scale}-{load_model}"
            ):
                os.makedirs(self.results_folder / f"cond_scale-{self.cond_scale}-{load_model}")
            filepath = f"cond_scale-{self.cond_scale}-{load_model}"
        else:
            print("Error: no model")
            return
        with torch.inference_mode():
            all_images_list = []
            val_imgs = []
            val_texts = []
            val_features = []
            idxs = []
            for (
                val_img,
                val_feature,
                val_text,
                val_graphormer_dict,
                idx,
            ) in self.val_dl:
                if val_img.shape[0] != self.batch_size:
                    batch_size = val_img.shape[0]
                else:
                    batch_size = self.batch_size
                val_img = val_img.to(self.device)
                val_feature = val_feature.to(self.device)
                val_graphormer_dict = {
                    k: v.to(self.device) for k, v in val_graphormer_dict.items()
                }
                val_imgs.append(val_img)
                val_texts.append(val_text)
                val_features.append(val_feature)
                idxs.append(idx)
                if self.use_graphormer:
                    val_text = None
                else:
                    val_graphormer_dict = None
                images = self.ema.ema_model.sample(
                    batch_size=batch_size,
                    feature=val_feature,
                    text=val_text,
                    graphormer_dict=val_graphormer_dict,
                    cond_scale=self.cond_scale,
                )
                all_images_list.append(images)

        micro_iou_list = []
        macro_iou_list = []
        for i in range(len(val_imgs)):
            for j in range(
                self.batch_size if i != len(val_imgs) - 1 else val_imgs[i].shape[0]
            ):
                if self.onehot:
                    img = convert_mult_to_rgb(all_images_list[i][j], val_features[i][j])
                    val_img = convert_mult_to_rgb(val_imgs[i][j], val_features[i][j])

                else:
                    new_image = torch.where(
                        val_features[i][j] > 0.5,
                        13 / 17,
                        all_images_list[i][j],
                    )
                    img = convert_gray_to_rgb(new_image)
                    val_img = convert_gray_to_rgb(val_imgs[i][j])
                    utils.save_image(
                        new_image,
                        str(
                            self.results_folder / filepath / f"sample-{idxs[i][j]}.png"
                        ),
                    )
                    utils.save_image(
                        val_imgs[i][j],
                        str(self.results_folder / filepath / f"real-{idxs[i][j]}.png"),
                    )
                micro_iou, macro_iou = cal_iou(img, val_img)
                micro_iou_list.append(micro_iou)
                macro_iou_list.append(macro_iou)

                utils.save_image(
                    img,
                    str(
                        self.results_folder / filepath / f"rgb_sample-{idxs[i][j]}.png"
                    ),
                )
                utils.save_image(
                    val_img,
                    str(self.results_folder / filepath / f"rgb_real-{idxs[i][j]}.png"),
                )
                with open(
                    self.results_folder / filepath / f"val_text-{idxs[i][j]}.txt",
                    "w",
                ) as f:
                    f.write(val_texts[i][j])
                utils.save_image(
                    val_features[i][j],
                    str(self.results_folder / filepath / f"feature-{idxs[i][j]}.png"),
                )
        micro_iou = sum(micro_iou_list) / len(micro_iou_list)
        macro_iou = sum(macro_iou_list) / len(macro_iou_list)
        print(f"micro_iou: {micro_iou}, macro_iou: {macro_iou}")
        with open(self.results_folder / filepath / f"iou.txt", "w") as f:
            for i in range(len(micro_iou_list)):
                f.write(
                    f"image{idxs[i//self.batch_size][i%self.batch_size]}-micro_iou: {micro_iou_list[i]}, macro_iou: {macro_iou_list[i]}\n"
                )
            f.write(f"micro_iou: {micro_iou}, macro_iou: {macro_iou}")

    def predict_load(self, load_model):
        self.load(load_model)
        self.ema.copy_params_from_model_to_ema()
        self.ema.ema_model.eval()

    def predict(self, feature, text, repredict=False):
        if repredict:
            self.cross_attention_edit.clear_all()
        seed_torch(self.cross_attention_edit.seed)
        # self.load(load_model)
        # self.ema.copy_params_from_model_to_ema()
        # self.ema.ema_model.eval()
        nodes = get_nodes(text)
        graph = get_dgl(nodes)
        attn_mask, node_feat, in_degree, out_degree, path_data, dist = collate([graph])
        graphormer_dict = {
            "attn_mask": attn_mask,
            "node_feat": node_feat,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "path_data": path_data,
            "dist": dist,
        }
        transform = T.Compose(
            [
                T.Lambda(partial(convert_image_to_fn, "L")),
                T.Resize(self.image_size),
                T.CenterCrop(self.image_size),
                T.ToTensor(),
            ]
        )
        feature = transform(feature)
        feature = feature.unsqueeze(0)
        feature = feature.to(self.device)
        for k, v in graphormer_dict.items():
            graphormer_dict[k] = v.to(self.device)
        if self.use_graphormer:
            text = None
        else:
            graphormer_dict = None
        image = self.ema.ema_model.sample(
            batch_size=1,
            feature=feature,
            text=text,
            graphormer_dict=graphormer_dict,
            cond_scale=self.cond_scale,
        )
        if not self.onehot:
            new_image = torch.where(
                feature[0] > 0.5,
                13 / 17,
                image[0],
            )
            img = convert_gray_to_rgb(new_image)
        ndarr = (
            img.mul(255)
            .add_(0.5)
            .clamp_(0, 255)
            .permute(1, 2, 0)
            .to("cpu", torch.uint8)
            .numpy()
        )
        im = Image.fromarray(ndarr)
        self.cross_attention_edit.end_of_generate()
        return im
