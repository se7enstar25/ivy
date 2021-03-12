import sys
import ivy

from .core import *
from . import nn
from .nn import *

# noinspection PyUnresolvedReferences
use = ivy.framework_handler.ContextManager(sys.modules[__name__])

Array = torch.Tensor
Variable = torch.Tensor
Device = torch.device
Dtype = torch.dtype

backend = 'torch'
