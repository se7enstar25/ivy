"""
Collection of PyTorch activation functions, wrapped to fit Ivy syntax and signature.
"""

from typing import Optional

# global
import numpy as np
import torch


def relu(x: torch.Tensor)\
        -> torch.Tensor:
    return torch.relu(x)


def leaky_relu(x: torch.Tensor, alpha: Optional[float] = 0.2)\
        -> torch.Tensor:
    return torch.nn.functional.leaky_relu(x, alpha)


def gelu(x, approximate: bool = True):
    if approximate:
        return 0.5 * x * (1 + torch.tanh(((2 / np.pi) ** 0.5) * (x + 0.044715 * x ** 3)))
    return torch.nn.functional.gelu(x)


def tanh(x: torch.Tensor)\
        -> torch.Tensor:
    return torch.tanh(x)



def sigmoid(x):
    return torch.sigmoid(x)


def softmax(x, axis: int = -1):
    return torch.softmax(x, axis)


def softplus(x: torch.Tensor)\
        -> torch.Tensor:
    return torch.nn.functional.softplus(x)
