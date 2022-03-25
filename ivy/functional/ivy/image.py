"""
Collection of image Ivy functions.
"""

# local
import ivy as ivy
import numpy as _np
from operator import mul as _mul
from functools import reduce as _reduce
from ivy.framework_handler import current_framework as _cur_framework
from typing import Union


# Extra #
# ------#

def stack_images(images, desired_aspect_ratio=(1, 1)):
    """
    Stacks a group of images into a combined windowed image, fitting the desired aspect ratio as closely as possible.

    :param images: Sequence of image arrays to be stacked *[batch_shape,height,width,dims]* .
    :type images: sequence of arrays
    :param desired_aspect_ratio: Desired aspect ratio of stacked image.
    :type desired_aspect_ratio: sequence of ints
    :return: Stacked image, suitable for viewing in a single window.
    """
    return _cur_framework(images[0]).stack_images(images, desired_aspect_ratio)


def bilinear_resample(x, warp):
    """
    Performs bilinearly re-sampling on input image.

    :param x: Input image *[batch_shape,h,w,dims]*.
    :type x: array
    :param warp: Warp array *[batch_shape,num_samples,2]*
    :type warp: array
    :return: Image after bilinear re-sampling.
    """
    return _cur_framework(x).bilinear_resample(x, warp)


def gradient_image(x):
    """
    Computes image gradients (dy, dx) for each channel.

    :param x: Input image *[batch_shape, h, w, d]* .
    :type x: array
    :return: Gradient images dy *[batch_shape,h,w,d]* and dx *[batch_shape,h,w,d]* .
    """
    return _cur_framework(x).gradient_image(x)


def float_img_to_uint8_img(x):
    """
    Converts an image of floats into a bit-cast 4-channel image of uint8s, which can be saved to disk.

    :param x: Input float image *[batch_shape,h,w]*.
    :type x: array
    :return: The new encoded uint8 image *[batch_shape,h,w,4]* .
    """
    x_np = ivy.to_numpy(x)
    x_shape = x_np.shape
    x_bytes = x_np.tobytes()
    x_uint8 = _np.frombuffer(x_bytes, _np.uint8)
    return ivy.array(_np.reshape(x_uint8, list(x_shape) + [4]).tolist())


def uint8_img_to_float_img(x):
    """
    Converts an image of uint8 values into a bit-cast float image.

    :param x: Input uint8 image *[batch_shape,h,w,4]*.
    :type x: array
    :return: The new float image *[batch_shape,h,w]*
    """
    x_np = ivy.to_numpy(x)
    x_shape = x_np.shape
    x_bytes = x_np.tobytes()
    x_float = _np.frombuffer(x_bytes, _np.float32)
    return ivy.array(_np.reshape(x_float, x_shape[:-1]).tolist())


def random_crop(x, crop_size, batch_shape=None, image_dims=None):
    """
    Randomly crops the input images.

    :param x: Input images to crop *[batch_shape,h,w,f]*
    :type x: array
    :param crop_size: The 2D crop size.
    :type crop_size: sequence of ints
    :param batch_shape: Shape of batch. Inferred from inputs if None.
    :type batch_shape: sequence of ints, optional
    :param image_dims: Image dimensions. Inferred from inputs in None.
    :type image_dims: sequence of ints, optional
    :return: The new cropped image *[batch_shape,nh,nw,f]*
    """

    x_shape = x.shape
    if batch_shape is None:
        batch_shape = x_shape[:-3]
    if image_dims is None:
        image_dims = x_shape[-3:-1]
    num_channels = x_shape[-1]
    flat_batch_size = _reduce(_mul, batch_shape, 1)

    # shapes as list
    batch_shape = list(batch_shape)
    image_dims = list(image_dims)
    margins = [img_dim - cs for img_dim, cs in zip(image_dims, crop_size)]

    # FBS x H x W x F
    x_flat = ivy.reshape(x, [flat_batch_size] + image_dims + [num_channels])

    # FBS x 1
    x_offsets = _np.random.randint(0, margins[0] + 1, [flat_batch_size]).tolist()
    y_offsets = _np.random.randint(0, margins[1] + 1, [flat_batch_size]).tolist()

    # list of 1 x NH x NW x F
    cropped_list = [img[..., xo:xo+crop_size[0], yo:yo+crop_size[1], :] for img, xo, yo
                    in zip(ivy.unstack(x_flat, 0, True), x_offsets, y_offsets)]

    # FBS x NH x NW x F
    flat_cropped = ivy.concatenate(cropped_list, 0)

    # BS x NH x NW x F
    return ivy.reshape(flat_cropped, batch_shape + crop_size + [num_channels])


def linear_resample(x: Union[ivy.Array, ivy.NativeArray], num_samples: int, axis: int = -1)\
        -> Union[ivy.Array, ivy.NativeArray]:
    """
    Performs linear re-sampling on input image.

    :param x: Input array
    :type x: array
    :param num_samples: The number of interpolated samples to take.
    :type num_samples: int
    :param axis: The axis along which to perform the resample. Default is last dimension.
    :type axis: int, optional
    :return: The array after the linear resampling.
    """
    return _cur_framework(x).linear_resample(x, num_samples, axis)
