#!/usr/bin/env python
"""
Plotting utilities
"""
import os
import matplotlib as mpl
import matplotlib.pyplot as plt

from .colorspace import OriginalColorSpace

#mpl.rcParams['axes.titlepad'] = 0


def load_image(image_path):
    """Load image helper function"""
    srgb = plt.imread(image_path)
    if len(srgb.shape) == 2:
        srgb = srgb[:, :, None]
    srgb = srgb[..., :3]
    return srgb


def compute_figure_dimensions(nspaces, img_shape) -> tuple:
    """Computes figure dimensions given image size"""
    dpi_guess = img_shape[0]/8
    if dpi_guess < 250:
        dpi_guess = 80
    else:
        dpi_guess = 300
    width = min(img_shape[0]/dpi_guess, 8)  #inches
    height = width / img_shape[1] * img_shape[0]

    layouts = {1: (1, 1),
               2: (1, 2),
               3: (1, 3),
               4: (2, 2),
               5: (2, 3),
               6: (2, 3),
               7: (3, 3),
               8: (3, 3),
               9: (3, 3)}
    nrows, ncols = layouts[nspaces]

    total_width = ncols * width
    total_height = (nrows * height) + 1
    return dict(nrows=nrows, ncols=ncols, figsize=(total_width, total_height))


def plot_colorspace(axes, colorspace, image) -> plt.Axes:
    """
    Given an matplotlib.pyplot.Axes object, a predefined ColorSpace
    object, plot the transformation of `image`
    """
    plot_params = dict(aspect=None)
    converted = colorspace.convert(image)
    axes.imshow(converted, **plot_params)

    figsize = axes.figure.get_size_inches()
    titlesize = ['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'] \
                + ['xx-large'] * 10
    titlesize = titlesize[int(figsize[0] / 4)]
    axes.set_title(colorspace.name, fontsize=titlesize)
    axes.set_xticks([])
    axes.set_yticks([])
    axes.axis('off')

    return axes

def plot_individually(original_path, colorspaces, outpath, **save_params):
    """
    Plot each colorspace in colorspaces in a different figure and save
    """
    original_image = load_image(original_path)
    image_shape = original_image.shape

    outname, outext = os.path.splitext(outpath)
    outext = 'png' if outext == '' else outext.strip('.')

    fig_shape = compute_figure_dimensions(1, image_shape)
    for colorspace in colorspaces:
        fig, axes = plt.subplots(**fig_shape)
        axes = plot_colorspace(axes, colorspace, original_image)

        fig.tight_layout()
        outfile = '.'.join((outname, colorspace.name.lower(), outext))
        fig.savefig(outfile, **save_params)

def plot_together(original_path, colorspaces, outpath,
                  show_original=True, **save_params):
    """
    Plot the original and all colorspaces on the same figure and save
    """
    original_image = load_image(original_path)
    image_shape = original_image.shape

    # hack to add original
    if show_original:
        colorspaces = [OriginalColorSpace()] + colorspaces

    nspaces = len(colorspaces)
    fig_shape = compute_figure_dimensions(nspaces, image_shape)
    fig, axarr = plt.subplots(**fig_shape)

    k = 0
    for k, (axes, colorspace) in enumerate(zip(axarr.flat, colorspaces)):
        axes = plot_colorspace(axes, colorspace, original_image)

    for axes in axarr.flatten()[k+1:]:
        axes.axis('off')

    fig.tight_layout()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=0.95,
                        wspace=0, hspace=0.05)

    fig.savefig(outpath, **save_params)
