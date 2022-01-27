import sys
import ivy
import numpy as np

from .core import *
from . import nn
from .nn import *

# noinspection PyUnresolvedReferences
use = ivy.framework_handler.ContextManager(sys.modules[__name__])

NativeArray = np.ndarray
NativeVariable = np.ndarray
Device = str
Dtype = np.dtype

# data types
int8 = np.dtype('int8')
int16 = np.dtype('int16')
int32 = np.dtype('int32')
int64 = np.dtype('int64')
uint8 = np.dtype('uint8')
uint16 = np.dtype('uint16')
uint32 = np.dtype('uint32')
uint64 = np.dtype('uint64')
bfloat16 = 'bfloat16'
float16 = np.dtype('float16')
float32 = np.dtype('float32')
float64 = np.dtype('float64')
# noinspection PyShadowingBuiltins
bool = np.dtype('bool')

backend = 'numpy'
