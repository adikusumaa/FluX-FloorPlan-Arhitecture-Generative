from denoising_diffusion_pytorch import Unet, GaussianDiffusion, Trainer, seed_torch
import os
import pickle


if __name__ == "__main__":
    seed_torch()
    os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    onehot = False
    if onehot:
        channels = 18
    else:
        channels = 1
    omit_graphormer = False
    results_folder = "./results/text21"
    train_num_workers = 8

    unet_dict = {
        "dim": 64,
        "cond_dim": 512,
        "dim_mults": (1, 2, 4, 8),
        "num_resnet_blocks": 3,
        "channels": channels,
        "cond_images_channels": 1,
        "layer_attns": (False, True, True, True),
        "omit_graphormer": omit_graphormer,
        "graphormer_layers": 1,
    }

    diffusion_dict = {
        "image_size": 64,
        "timesteps": 1000,
        "sampling_timesteps": 50,
        "cond_drop_prob": 0.1,
    }

    trainer_dict = {
        "train_batch_size": 32,
        "train_lr": 8e-5,
        "train_num_steps": 500000,
        "gradient_accumulate_every": 1,
        "ema_decay": 0.995,
        "save_and_sample_every": 5000,
        "augment_flip": False,
        "cond_scale": 1,
        "convert_image_to": "L",
        "mask": 0.1,
        "onehot": onehot,
    }

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    model = Unet(**unet_dict)

    diffusion = GaussianDiffusion(model, **diffusion_dict)

    trainer = Trainer(
        diffusion,
        "../chathousediffusion/data/0531/image",
        "../chathousediffusion/data/0531/mask",
        "../chathousediffusion/data/0531/text",
        **trainer_dict,
        results_folder=results_folder,
        train_num_workers=train_num_workers
    )

    
    with open(os.path.join(results_folder, "params.pkl"), "wb") as f:
        pickle.dump(
            {
                "unet_dict": unet_dict,
                "diffusion_dict": diffusion_dict,
                "trainer_dict": trainer_dict,
            },
            f,
        )

    trainer.train()
