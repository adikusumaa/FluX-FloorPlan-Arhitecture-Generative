from denoising_diffusion_pytorch import Unet, GaussianDiffusion, Trainer, seed_torch
import os
import pickle
from PIL import Image
import pandas as pd


if __name__ == "__main__":

    os.environ["CUDA_VISIBLE_DEVICES"] = "2"
    results_folder = "./results/text21"
    train_num_workers = 0
    with open(os.path.join(results_folder, "params.pkl"), "rb") as f:
        params = pickle.load(f)

    model = Unet(**params["unet_dict"])

    # params["diffusion_dict"]["sampling_timesteps"] = 10

    diffusion = GaussianDiffusion(model, **params["diffusion_dict"])

    trainer = Trainer(
        diffusion,
        "../chat_test_data/0614-kimi/image",
        "../chat_test_data/0614-kimi/mask",
        "../chat_test_data/0614-kimi/text",
        **params["trainer_dict"],
        results_folder=results_folder,
        train_num_workers=train_num_workers,
        mode="val",
    )

    seed_torch()
    trainer.val(load_model=98)
    