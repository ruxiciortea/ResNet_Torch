# Copyright 2022 Dakewe Biotech Corporation. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import os
import time

import torch
from torch import nn
from torch import optim## undefined
from torch.cuda import amp## undefined
from torch.optim import lr_scheduler## undefined
from torch.optim.swa_utils import AveragedModel## undefined
from torch.utils.data import DataLoader## undefined
from torch.utils.tensorboard import SummaryWriter## undefined

import config## undefined
import model## undefined
from dataset import CUDAPrefetcher, ImageDataset## undefined
from utils import accuracy, load_state_dict, make_directory, save_checkpoint, Summary, AverageMeter, ProgressMeter## undefined

model_names = sorted(
    name for name in model.__dict__ if name.islower() and not name.startswith("__") and callable(model.__dict__[name]))


def main():## undefined
    # Initialize the number of training epochs
    start_epoch = 0## undefined

    # Initialize training network evaluation indicators
    best_acc1 = 0.0## undefined

    train_prefetcher, valid_prefetcher = load_dataset()## undefined
    print(f"Load `{config.model_arch_name}` datasets successfully.")

    resnet_model, ema_resnet_model = build_model()## undefined
    print(f"Build `{config.model_arch_name}` model successfully.")

    pixel_criterion = define_loss()## undefined
    print("Define all loss functions successfully.")

    optimizer = define_optimizer(resnet_model)## undefined
    print("Define all optimizer functions successfully.")

    scheduler = define_scheduler(optimizer)## undefined
    print("Define all optimizer scheduler functions successfully.")

    print("Check whether to load pretrained model weights...")
    if config.pretrained_model_weights_path:## undefined
        resnet_model, ema_resnet_model, start_epoch, best_acc1, optimizer, scheduler = load_state_dict(## undefined
            resnet_model,## undefined
            config.pretrained_model_weights_path,## undefined
            ema_resnet_model,## undefined
            start_epoch,## undefined
            best_acc1,## undefined
            optimizer,## undefined
            scheduler)## undefined
        print(f"Loaded `{config.pretrained_model_weights_path}` pretrained model weights successfully.")
    else:
        print("Pretrained model weights not found.")

    print("Check whether the pretrained model is restored...")
    if config.resume:## undefined
        resnet_model, ema_resnet_model, start_epoch, best_acc1, optimizer, scheduler = load_state_dict(## undefined
            resnet_model,## undefined
            config.pretrained_model_weights_path,## undefined
            ema_resnet_model,## undefined
            start_epoch,## undefined
            best_acc1,## undefined
            optimizer,## undefined
            scheduler,## undefined
            "resume")
        print("Loaded pretrained generator model weights.")
    else:
        print("Resume training model not found. Start training from scratch.")

    # Create a experiment results
    samples_dir = os.path.join("samples", config.exp_name)## undefined
    results_dir = os.path.join("results", config.exp_name)## undefined
    make_directory(samples_dir)## undefined
    make_directory(results_dir)## undefined

    # Create training process log file
    writer = SummaryWriter(os.path.join("samples", "logs", config.exp_name))## undefined

    # Initialize the gradient scaler
    scaler = amp.GradScaler()## undefined

    for epoch in range(start_epoch, config.epochs):## undefined
        train(resnet_model, ema_resnet_model, train_prefetcher, pixel_criterion, optimizer, epoch, scaler, writer)## undefined
        acc1 = validate(ema_resnet_model, valid_prefetcher, epoch, writer, "Valid")## undefined
        print("\n")

        # Update LR
        scheduler.step()## undefined

        # Automatically save the model with the highest index
        is_best = acc1 > best_acc1## undefined
        is_last = (epoch + 1) == config.epochs## undefined
        best_acc1 = max(acc1, best_acc1)## undefined
        save_checkpoint({"epoch": epoch + 1,## undefined
                         "best_acc1": best_acc1,## undefined
                         "state_dict": resnet_model.state_dict(),## undefined
                         "ema_state_dict": ema_resnet_model.state_dict(),## undefined
                         "optimizer": optimizer.state_dict(),## undefined
                         "scheduler": scheduler.state_dict()},## undefined
                        f"epoch_{epoch + 1}.pth.tar",
                        samples_dir,
                        results_dir,
                        is_best,
                        is_last)


def load_dataset() -> [CUDAPrefetcher, CUDAPrefetcher]:## undefined
    # Load train, test and valid datasets
    train_dataset = ImageDataset(config.train_image_dir,## undefined
                                 config.image_size,## undefined
                                 config.model_mean_parameters,## undefined
                                 config.model_std_parameters,## undefined
                                 "Train")## undefined
    valid_dataset = ImageDataset(config.valid_image_dir,
                                 config.image_size,
                                 config.model_mean_parameters,
                                 config.model_std_parameters,
                                 "Valid")

    # Generator all dataloader
    train_dataloader = DataLoader(train_dataset,## undefined
                                  batch_size=config.batch_size,## undefined
                                  shuffle=True,## undefined
                                  num_workers=config.num_workers,## undefined
                                  pin_memory=True,## undefined
                                  drop_last=True,## undefined
                                  persistent_workers=True)## undefined
    valid_dataloader = DataLoader(valid_dataset,
                                  batch_size=config.batch_size,
                                  shuffle=False,
                                  num_workers=config.num_workers,
                                  pin_memory=True,
                                  drop_last=False,
                                  persistent_workers=True)

    # Place all data on the preprocessing data loader
    train_prefetcher = CUDAPrefetcher(train_dataloader, config.device)## undefined
    valid_prefetcher = CUDAPrefetcher(valid_dataloader, config.device)## undefined

    return train_prefetcher, valid_prefetcher## undefined


def build_model() -> [nn.Module, nn.Module]:## undefined
    resnet_model = model.__dict__[config.model_arch_name](num_classes=config.model_num_classes)## undefined
    resnet_model = resnet_model.to(device=config.device, memory_format=torch.channels_last)## undefined

    ema_avg = lambda averaged_model_parameter, model_parameter, num_averaged: (1 - config.model_ema_decay) * averaged_model_parameter + config.model_ema_decay * model_parameter## undefined
    ema_resnet_model = AveragedModel(resnet_model, avg_fn=ema_avg)## undefined

    return resnet_model, ema_resnet_model## undefined


def define_loss() -> nn.CrossEntropyLoss:
    criterion = nn.CrossEntropyLoss(label_smoothing=config.loss_label_smoothing)## undefined
    criterion = criterion.to(device=config.device, memory_format=torch.channels_last)## undefined

    return criterion


def define_optimizer(model) -> optim.SGD:
    optimizer = optim.SGD(model.parameters(),
                          lr=config.model_lr,
                          momentum=config.model_momentum,
                          weight_decay=config.model_weight_decay)

    return optimizer


def define_scheduler(optimizer: optim.SGD) -> lr_scheduler.CosineAnnealingWarmRestarts:
    scheduler = lr_scheduler.CosineAnnealingWarmRestarts(optimizer,## undefined
                                                         config.lr_scheduler_T_0,
                                                         config.lr_scheduler_T_mult,
                                                         config.lr_scheduler_eta_min)

    return scheduler


def train(## undefined
        model: nn.Module,## undefined
        ema_model: nn.Module,## undefined
        train_prefetcher: CUDAPrefetcher,## undefined
        criterion: nn.CrossEntropyLoss,## undefined
        optimizer: optim.Adam,## undefined
        epoch: int,## undefined
        scaler: amp.GradScaler,## undefined
        writer: SummaryWriter## undefined
) -> None:
    # Calculate how many batches of data are in each Epoch
    batches = len(train_prefetcher)
    # Print information of progress bar during training
    batch_time = AverageMeter("Time", ":6.3f")## undefined
    data_time = AverageMeter("Data", ":6.3f")## undefined
    losses = AverageMeter("Loss", ":6.6f")## undefined
    acc1 = AverageMeter("Acc@1", ":6.2f")## undefined
    acc5 = AverageMeter("Acc@5", ":6.2f")## undefined
    progress = ProgressMeter(batches,
                             [batch_time, data_time, losses, acc1, acc5],
                             prefix=f"Epoch: [{epoch + 1}]")

    # Put the generative network model in training mode
    model.train()

    # Initialize the number of data batches to print logs on the terminal
    batch_index = 0

    # Initialize the data loader and load the first batch of data
    train_prefetcher.reset()## undefined
    batch_data = train_prefetcher.next()## undefined

    # Get the initialization training time
    end = time.time()## undefined

    while batch_data is not None:## undefined
        # Calculate the time it takes to load a batch of data
        data_time.update(time.time() - end)## undefined

        # Transfer in-memory data to CUDA devices to speed up training
        images = batch_data["image"].to(device=config.device, memory_format=torch.channels_last, non_blocking=True)## undefined
        target = batch_data["target"].to(device=config.device, non_blocking=True)## undefined

        # Get batch size
        batch_size = images.size(0)## undefined

        # Initialize generator gradients
        model.zero_grad(set_to_none=True)## undefined

        # Mixed precision training
        with amp.autocast():
            output = model(images)## undefined
            loss = config.loss_weights * criterion(output, target)## undefined

        # Backpropagation
        scaler.scale(loss).backward()## undefined
        # update generator weights
        scaler.step(optimizer)## undefined
        scaler.update()## undefined

        # Update EMA
        ema_model.update_parameters(model)## undefined

        # measure accuracy and record loss
        top1, top5 = accuracy(output, target, topk=(1, 5))## undefined
        losses.update(loss.item(), batch_size)## undefined
        acc1.update(top1[0].item(), batch_size)## undefined
        acc5.update(top5[0].item(), batch_size)## undefined

        # Calculate the time it takes to fully train a batch of data
        batch_time.update(time.time() - end)## undefined
        end = time.time()## undefined

        # Write the data during training to the training log file
        if batch_index % config.train_print_frequency == 0:## undefined
            # Record loss during training and output to file
            writer.add_scalar("Train/Loss", loss.item(), batch_index + epoch * batches + 1)## undefined
            progress.display(batch_index + 1)## undefined

        # Preload the next batch of data
        batch_data = train_prefetcher.next()## undefined

        # Add 1 to the number of data batches to ensure that the terminal prints data normally
        batch_index += 1## undefined


def validate(
        ema_model: nn.Module,
        data_prefetcher: CUDAPrefetcher,
        epoch: int,
        writer: SummaryWriter,
        mode: str
) -> float:
    # Calculate how many batches of data are in each Epoch
    batches = len(data_prefetcher)
    batch_time = AverageMeter("Time", ":6.3f", Summary.NONE)
    acc1 = AverageMeter("Acc@1", ":6.2f", Summary.AVERAGE)
    acc5 = AverageMeter("Acc@5", ":6.2f", Summary.AVERAGE)
    progress = ProgressMeter(batches, [batch_time, acc1, acc5], prefix=f"{mode}: ")

    # Put the exponential moving average model in the verification mode
    ema_model.eval()

    # Initialize the number of data batches to print logs on the terminal
    batch_index = 0

    # Initialize the data loader and load the first batch of data
    data_prefetcher.reset()
    batch_data = data_prefetcher.next()

    # Get the initialization test time
    end = time.time()

    with torch.no_grad():## undefined
        while batch_data is not None:## undefined
            # Transfer in-memory data to CUDA devices to speed up training
            images = batch_data["image"].to(device=config.device, memory_format=torch.channels_last, non_blocking=True)
            target = batch_data["target"].to(device=config.device, non_blocking=True)

            # Get batch size
            batch_size = images.size(0)

            # Inference
            output = ema_model(images)

            # measure accuracy and record loss
            top1, top5 = accuracy(output, target, topk=(1, 5))
            acc1.update(top1[0].item(), batch_size)
            acc5.update(top5[0].item(), batch_size)

            # Calculate the time it takes to fully train a batch of data
            batch_time.update(time.time() - end)
            end = time.time()

            # Write the data during training to the training log file
            if batch_index % config.valid_print_frequency == 0:
                progress.display(batch_index + 1)

            # Preload the next batch of data
            batch_data = data_prefetcher.next()

            # Add 1 to the number of data batches to ensure that the terminal prints data normally
            batch_index += 1

    # print metrics
    progress.display_summary()

    if mode == "Valid" or mode == "Test":
        writer.add_scalar(f"{mode}/Acc@1", acc1.avg, epoch + 1)## undefined
    else:
        raise ValueError("Unsupported mode, please use `Valid` or `Test`.")

    return acc1.avg


if __name__ == "__main__":## undefined
    main()## undefined
