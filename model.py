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
from typing import Any, List, Type, Union, Optional## import some data types

import torch## import torch
from torch import Tensor## import tensor class
from torch import nn## import neural network module 

__all__ = [## define the classes which are going to be shown when importing * from the current module
    "ResNet",## ResNet class
    "resnet18",
]


class _BasicBlock(nn.Module):## define the _BasicClock class whichi inherits from nn.Module (the underscore might mean that the class is not intented to be accessed outside this file)
    expansion: int = 1## defines the expansion attribute of the calss

    def __init__(## class initializer
            self,## object to init
            in_channels: int,## input channels attribute
            out_channels: int,## outer channels attribute
            stride: int,## stride attribute
            downsample: Optional[nn.Module] = None,## downsample optional attribute
            groups: int = 1,## groups optional attribute
            base_channels: int = 64,## base channel optional attribute
    ) -> None:
        super(_BasicBlock, self).__init__()## calles the init of the parent class
        self.stride = stride## set object's stride attribute
        self.downsample = downsample## set object's downsample attribute
        self.groups = groups## set object's groups atribute
        self.base_channels = base_channels## set object's base_channels attribute

        self.conv1 = nn.Conv2d(in_channels, out_channels, (3, 3), (stride, stride), (1, 1), bias=False)## applies a 2D convolution over an input signal composed of several input planes
        self.bn1 = nn.BatchNorm2d(out_channels)## applies Batch Normalization over a 4D input
        self.relu = nn.ReLU(True)## applies relu on the input
        self.conv2 = nn.Conv2d(out_channels, out_channels, (3, 3), (1, 1), (1, 1), bias=False)## apply the 2D convolution again
        self.bn2 = nn.BatchNorm2d(out_channels)## and the normalization again

    def forward(self, x: Tensor) -> Tensor:
        identity = x

        out = self.conv1(x)## apply a 1D convolution on the input
        out = self.bn1(out)## apply a Batch Normalization on the input
        out = self.relu(out)## apply relu on the input

        out = self.conv2(out)## convolution again
        out = self.bn2(out)## and normalization again

        if self.downsample is not None:## if downsample is present
            identity = self.downsample(x)## apply it on the input

        out = torch.add(out, identity)## add the identity to the torch
        out = self.relu(out)## apply relu again on the data being processed

        return out


class _Bottleneck(nn.Module):## defines a fileprivat class whichi inherits from nn.Module
    expansion: int = 4## defines the expansion attribute of the calss

    def __init__(
            # downsampling reduces the dataset to a more manageable size
            self,## object to be initialized
            in_channels: int,## input channels
            out_channels: int,## output channels
            stride: int,## stride
            downsample: Optional[nn.Module] = None,## optional downstride
            groups: int = 1,## optional groups
            base_channels: int = 64,## optional base_channels
    ) -> None:
        super(_Bottleneck, self).__init__()## call the init of the parent class
        self.stride = stride## set the stride attribute with the one provided to the init function
        self.downsample = downsample## set the downsample attribute with the one provided to the init function
        self.groups = groups## set the groups attribute with the one provided to the init function
        self.base_channels = base_channels## set the base_channels attribute with the one provided to the init function

        channels = int(out_channels * (base_channels / 64.0)) * groups## calculate the channels based on some formula

        self.conv1 = nn.Conv2d(in_channels, channels, (1, 1), (1, 1), (0, 0), bias=False)## applies a 2D convolution on the input channels
        self.bn1 = nn.BatchNorm2d(channels)## applies Batch Normalization over a 4D on the channels
        self.conv2 = nn.Conv2d(channels, channels, (3, 3), (stride, stride), (1, 1), groups=groups, bias=False)## applies a 2D convolution on the channels
        self.bn2 = nn.BatchNorm2d(channels)
        self.conv3 = nn.Conv2d(channels, int(out_channels * self.expansion), (1, 1), (1, 1), (0, 0), bias=False)## applies a 2D convolution on the channels
        self.bn3 = nn.BatchNorm2d(int(out_channels * self.expansion))## applies Batch Normalization over a 4D on the output channels
        self.relu = nn.ReLU(True)## creates an instance of relu with the inplace argument set to true (meaning that the result is set on the input, not on a new variable)

    def forward(self, x: Tensor) -> Tensor:## the function that does the forward pass, feeding the input into the model
        identity = x## identity tensor, rememebering it

        out = self.conv1(x)## apply the 2D convolution on the input
        out = self.bn1(out)## then the Batch Normalization
        out = self.relu(out)## then the relu (all on top of eahc other)

        out = self.conv2(out)## convolution again
        out = self.bn2(out)## normalization again
        out = self.relu(out)## relu again

        out = self.conv3(out)## 3D convolution
        out = self.bn3(out)## normalization again

        if self.downsample is not None:## is downsample is present
            identity = self.downsample(x)## apply it on the input

        out = torch.add(out, identity)## add the identity to the torch
        out = self.relu(out)## apply relu once again

        return out


class ResNet(nn.Module):## defines the ResNet class whichi inherits from nn.Module

    def __init__(
            self,## object to init
            arch_cfg: List[int],## atch_cft attribute
            block: Type[Union[_BasicBlock, _Bottleneck]],## block attribute
            groups: int = 1,## groups optional attribute
            channels_per_group: int = 64,## channels_per_group optional attribute
            num_classes: int = 1000,## num_classes optional attribute
    ) -> None:
        super(ResNet, self).__init__()## call the init of the super class
        self.in_channels = 64## set the input channels of the object to 64
        self.dilation = 1## set the dilatation to 1
        self.groups = groups## set the groups to the provided parameter
        self.base_channels = channels_per_group## set the base_channels to the provided parameter

        self.conv1 = nn.Conv2d(3, self.in_channels, (7, 7), (2, 2), (3, 3), bias=False)## apply the 2D convolution on the input channels
        self.bn1 = nn.BatchNorm2d(self.in_channels)## and the normalization
        self.relu = nn.ReLU(True)## creates an instance of relu with the inplace argument set to true (meaning that the result is set on the input, not on a new variable)
        self.maxpool = nn.MaxPool2d((3, 3), (2, 2), (1, 1))## creates an instance of a 2D max pooling with the given parameters

        self.layer1 = self._make_layer(arch_cfg[0], block, 64, 1)## undefined
        self.layer2 = self._make_layer(arch_cfg[1], block, 128, 2)## undefined
        self.layer3 = self._make_layer(arch_cfg[2], block, 256, 2)## undefined
        self.layer4 = self._make_layer(arch_cfg[3], block, 512, 2)## undefined

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))## undefined

        self.fc = nn.Linear(512 * block.expansion, num_classes)## undefined

        # Initialize neural network weights
        self._initialize_weights()## undefined

    def _make_layer(## undefined
            self,
            repeat_times: int,## undefined
            block: Type[Union[_BasicBlock, _Bottleneck]],
            channels: int,
            stride: int = 1,
    ) -> nn.Sequential:
        downsample = None

        if stride != 1 or self.in_channels != channels * block.expansion:## undefined
            downsample = nn.Sequential(## undefined
                nn.Conv2d(self.in_channels, channels * block.expansion, (1, 1), (stride, stride), (0, 0), bias=False),## undefined
                nn.BatchNorm2d(channels * block.expansion),## undefined
            )

        layers = [## undefined
            block(## undefined
                self.in_channels,## undefined
                channels,## undefined
                stride,## undefined
                downsample,## undefined
                self.groups,## undefined
                self.base_channels## undefined
            )
        ]
        self.in_channels = channels * block.expansion## undefined
        for _ in range(1, repeat_times):## undefined
            layers.append(## undefined
                block(
                    self.in_channels,## undefined
                    channels,## undefined
                    1,## undefined
                    None,
                    self.groups,
                    self.base_channels,
                )
            )

        return nn.Sequential(*layers)## undefined

    def forward(self, x: Tensor) -> Tensor:
        out = self._forward_impl(x)## undefined

        return out

    # Support torch.script function
    def _forward_impl(self, x: Tensor) -> Tensor:## undefined
        out = self.conv1(x)## undefined
        out = self.bn1(out)## undefined
        out = self.relu(out)## undefined
        out = self.maxpool(out)## undefined

        out = self.layer1(out)## undefined
        out = self.layer2(out)## undefined
        out = self.layer3(out)## undefined
        out = self.layer4(out)## undefined

        out = self.avgpool(out)## undefined
        out = torch.flatten(out, 1)## undefined
        out = self.fc(out)## undefined

        return out

    def _initialize_weights(self) -> None:## undefined
        for module in self.modules():## undefined
            if isinstance(module, nn.Conv2d):## undefined
                nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")## undefined
            elif isinstance(module, (nn.BatchNorm2d, nn.GroupNorm)):## undefined
                nn.init.constant_(module.weight, 1)## undefined
                nn.init.constant_(module.bias, 0)## undefined


def resnet18(**kwargs: Any) -> ResNet:## undefined
    model = ResNet([2, 2, 2, 2], _BasicBlock, **kwargs)## undefined

    return model


def resnet34(**kwargs: Any) -> ResNet:
    model = ResNet([3, 4, 6, 3], _BasicBlock, **kwargs)

    return model


def resnet50(**kwargs: Any) -> ResNet:
    model = ResNet([3, 4, 6, 3], _Bottleneck, **kwargs)

    return model


def resnet101(**kwargs: Any) -> ResNet:
    model = ResNet([3, 4, 23, 3], _Bottleneck, **kwargs)

    return model


def resnet152(**kwargs: Any) -> ResNet:
    model = ResNet([3, 8, 36, 3], _Bottleneck, **kwargs)

    return model
