"""
Collection of MXNet activation functions, wrapped to fit Ivy syntax and signature.
"""

# global
import mxnet as _mx

relu = _mx.nd.relu
leaky_relu = lambda x, alpha=0.2: _mx.nd.LeakyReLU(x, slope=alpha)
tanh = _mx.nd.tanh
sigmoid = _mx.nd.sigmoid
softmax = _mx.nd.softmax
softplus = lambda x: _mx.nd.log(_mx.nd.exp(x) + 1)
