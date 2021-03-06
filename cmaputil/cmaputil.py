# -*- coding: utf-8 -*-
"""
Utilities for working with standard colormaps

@author: Jamie R. Nunez
(C) 2017 - Pacific Northwest National Laboratory
"""
#%% Imports
from __future__ import print_function
from math import floor, sqrt, ceil
from os.path import exists

import matplotlib.cm as cm # Used with eval()
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D # Used to make 3D axes
import numpy as np
import scipy

from colorspacious import cspace_convert

#%% Global Variables
CMAPS = ['Accent', 'Blues', 'BrBG', 'BuGn', 'BuPu', 'CMRmap', 'Dark2', 'GnBu',
         'Greens', 'Greys', 'OrRd', 'Oranges', 'PRGn', 'Paired', 'Pastel1',
         'Pastel2', 'PiYG', 'PuBu', 'PuBuGn', 'PuOr', 'PuRd', 'Purples',
         'RdBu', 'RdGy', 'RdPu', 'RdYlBu', 'RdYlGn', 'Reds', 'Set1', 'Set2',
         'Set3', 'Spectral', 'Wistia', 'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd',
         'afmhot', 'autumn', 'binary', 'bone', 'brg', 'bwr', 'cool',
         'coolwarm', 'copper', 'cubehelix', 'flag', 'gist_earth', 'gist_gray',
         'gist_ncar', 'gist_stern', 'gist_yarg', 'gnuplot',
         'gnuplot2', 'gray', 'hot', 'hsv', 'inferno', 'jet', 'magma',
         'nipy_spectral', 'ocean', 'pink', 'plasma', 'prism', 'rainbow',
         'seismic', 'spectral', 'spring', 'summer', 'terrain', 'viridis',
         'winter']
CSPACE1 = 'sRGB1'
CSPACE2 = 'CAM02-UCS'
FLABEL = 20  # font size for labels (title and axis labels)
FAX = 16  # font size for numbers on axes

#%% Colormap Processing Functions


def _check_cmap(cmap):
    '''
    Checks passed cmap name. If it is invalid, throws ValueError.
    Otherwise, it does nothing.

    To use a custom-made colormap, save it to a .npy file then use the
    path and file name (e.g. 'path\example' for path\example.npy') as
    the cmap variable name.

    A name is considered invalid when not included in the CMAPS
    variable and a .npy file with its name could not be found. This
    list is manually created so it could be out of date depending on
    the time of this code's release.
    '''

    if cmap is None or cmap not in CMAPS:
        if not exists(cmap + '.npy'):
            raise ValueError(cmap + ' not a valid colormap name.')
    return


def create_isoluminant_map(data):
    '''
    Takes in a colormap (name or RGB values) and cycles through all
    possible intensity values that are valid for all a',b' pairs
    present in the original colormap. Full matrix returned can be
    plotted to view range of intensities valid for that colormap as a
    whole or a single colormap within the returned matrix (selected
    using m[:, :, x], which represents one isoluminant colormap) can be
    plotted alone.

    Parameters
    -----------
    data: str or ndarray
        Colormap name or RGB values

    Returns
    -----------
    rgb: ndarray, dimensions = (3, 256, X)
        Isoluminant colormap matrix containing X isoluminant colormaps

    '''

    _, jab = get_rgb_jab(data)
    minJ, maxJ = find_J_bounds(jab, report=False)

    # Exit if isoluminant map failed
    if minJ is None:
        return None

    # Continue if passed
    h = int(maxJ) - int(minJ)
    rgb = np.zeros((jab.shape[0], jab.shape[1], h))
    for j in range(h):
        jab[0, :] = int(minJ) + j
        rgb[:, :, j] = convert(jab, CSPACE2, CSPACE1)

    return rgb


def _find_J_bounds(j, a, b):
    '''
    Tests J' values against a'b' pairs to determine the max range,
    within the range given by [j, maxj], of J's that can be used with
    this pair. Recursive function.

    All J'a'b' pairs will convert to a RGB value but not all of these
    values fall within normal color space so they are tested to be
    between 0 and 255.
    '''

    test_rgb = cspace_convert([j, a, b], CSPACE2, CSPACE1)

    if _valid_rgb(test_rgb[0]) and _valid_rgb(test_rgb[1]) and \
       _valid_rgb(test_rgb[2]):
        return True
    return False


def find_J_bounds(data, report=True):
    '''
    Takes in colormap name or J'a'b' values and finds the maximum and
    minumum J' values that all a'b' pairs fit with. This has to be
    done since the CAM02-UCS colorspace is not a perfect square.

    Invalid colormap names throw a ValueError. Refer to
    _check_cmap for more information.

    Parameters
    -----------
    data: str or ndarray
        Colormap name or J'a'b' ndarray generated by get_rgb_jab
    report: boolean
        Decides whether results should be printed to the console.
        Default value is True.

    Returns
    -----------
    minJ : int
        Lowest J' value that works with all a'b' pairs.
    maxJ : int
        Highest J' value that works with all a'b' pairs
    '''

    # Read in J'a'b' values from variable directly or generate them
    if type(data) == str:
        _, m = get_rgb_jab(data)
    else:
        m = np.copy(data)

    # Test each a'b' pair for their max and min J'
    minJ = 0
    maxJ = 100
    # possible bug here when len(m.shape) == 1?
    if m.shape[1] > 3:
        for i in range(m.shape[1]):
            a = m[1, i]
            b = m[2, i]
            passed = []
            J = minJ
            while J <= maxJ:
                if _find_J_bounds(J, a, b):
                    passed.append(J)
                while _find_J_bounds(J + 5, a, b):
                    passed.append(J)
                    J += 5
                J += 0.1
            if len(passed) > 0:
                minJ = max(minJ, min(passed))
                maxJ = min(maxJ, max(passed))

    else:
        a = m[1]
        b = m[2]
        passed = []
        J = 0.5
        while J <= 100:
            if _find_J_bounds(J, a, b):
                passed.append(J)
            while _find_J_bounds(J + 5, a, b):
                passed.append(J)
                J += 5
            J += 0.1
        minJ = min(passed)
        maxJ = max(passed)

    if report:
        print('Passed: ' + str([minJ, maxJ]))
    return minJ, maxJ


def convert(data, from_space, to_space):
    '''
    Takes a single color value or matrix of values and converts to the
    desired colorspace

    Parameters
    -----------
    data: 3 x COL array
        Colormap name OR array with complete color data. Invalid
        colormap names throw a ValueError. Refer to _check_cmap for
        more information.
    from_space: str
        Colorspace the current color value(s) reside(s) in
    to_space: str
        Colorspace to convert the color value(s) to

    Returns
    -----------
    n : 3 x COL ndarray
        RGB values for each converted color value
    '''
    if from_space == CSPACE1:
        data = np.clip(data, 0, 1)
    new = cspace_convert(data.T, from_space, to_space).T
    if to_space == CSPACE1:
        new = np.clip(new, 0, 1)
    return new


def _get_rgb(cmap):
    # Get RGB Values
    if cmap in CMAPS:
        rgb = np.zeros((3, 256))
        c = eval('cm.' + cmap)
        for i in range(256):
            rgb[:, i] = c(i)[:-1]
    else:
        rgb = np.load(cmap + '.npy')
        if rgb.shape[0] != 3:
            rgb = rgb.T
    return rgb


def get_rgb_jab(data, calc_jab=True):
    '''
    Accepts cmap name or data and creates its corresponding RGB and J'a'b'
    matrices.

    Parameters
    -----------
    data: string or 3 x 256 array
        Colormap name OR array with complete color data. Invalid
        colormap names throw a ValueError. Refer to _check_cmap for
        more information.

    Returns
    -----------
    rgb : 3 x 256 ndarray
        RGB values for each value in the colormap
    jab : 3 x 256 ndarray
        J'a'b' values corresponding to each RGB value
    '''

    # Colormap name passed in - get RGB values
    if type(data) == str:
        cmap = data
        _check_cmap(cmap)
        rgb = _get_rgb(cmap)

    # RGB values passed in
    else:
        rgb = data

    rgb = np.clip(rgb, 0, 1)

    if calc_jab:
        # Convert RGB -> J'a'b'
        jab = convert(rgb, CSPACE1, CSPACE2)

        # Ensure J' is valid (between 0 and 100)
        jab[0, :] = np.clip(jab[0, :], 0, 100)
    else:
        jab = None

    return rgb, jab


#%% Image Processing Functions
def _adjust_bounds(a, minimum, maximum):
    '''
    Takes in an array and adjusts all values to be between the min and
    max values. Relative magnitude does not change (i.e., numbers still
    keep their place in the overall order of min to max values).

    Parameters
    -----------
    a : array
        Array to be adjusted
    minimum : int
        Minimum value for new array
    maximum : int
        Maximum value for new array

    Returns
    -----------
    new_array : ndarray
        Returns new array (same size as the original) with all values
        adjusted to be between the min and max value.
    '''
    r = maximum - minimum
    new_array = np.copy(a)
    mult = float(r) / float(np.max(new_array) - np.min(new_array))
    new_array *= mult  # Change data range
    new_array += minimum - np.min(new_array)  # Start at min value
    return new_array


def bound(a, high, low):
    '''
    Forces all values within an array to be between a specified high
    and low value. Values that are smaller than the low value are set
    to equal the low value and values that are larger than the high
    value are set to equal the high value. Numbers already in this
    range are not changed.

    It helps to use the normalize function first to have values based
    on their std. dev. so outliers can be easily dealt with.

    Parameters
    -----------
    a : array
        Array to be bounded
    high : float
        Upper bound
    low : float
        Lower bound

    Returns
    -----------
    new_array : array
        Bounded array. Same size as the original array.
    '''

    new_array = np.copy(a)
    new_array[new_array > high] = high
    new_array[new_array < low] = low
    return new_array


def mix_images(img1, img2, cmap, high, low, name=None, maprevolve=False):
    '''
    First, checks if passed colormap is valid for mixing images. It is
    not valid if the colormap itself is not valid or if each a'b' pair
    can not cycle through a range of J' values. See find_J_bounds for
    more information.

    Next, plots the colormap with all possible J' values for each a'b'
    pair. Can do a full 3D rotation if needed but this makes
    computing time about 10X longer.

    Lastly, creates a new image with colors corresponding to img1
    values and lightness values corresponding to img2.

    Invalid colormap names throw a ValueError. Refer to
    _check_cmap for more information.

    Parameters
    -----------
    img1 : array
        Image to set color
    img2 : array
        Image to set lightness
    cmap : string
        Name of colormap to be used. Note: not all colormaps will work.
    high : float
        Max cutoff for img1 values (all values higher will be set to
        this). Keeps outliers from affecting the quality of the output
    low : float
        Min cutoff for img1 values (all values lower will be set to
        this and then colored black in the final image (as background)
    name : string
        Name of file to be saved to. Make sure to include the file type
        (e.g. .png, .pdf). If name is None, the file will not be saved.
        Default value is None.
    maprevolve : boolean
        Decides whether full 3D rotation images will be plotted and
        saved for the 3D colormap plot. Extends total computation time
        about 10X. Is considered False is name is None. Default value
        is False.

    Returns
    -----------
    img1_rgb : ndarray
        Img1 colored using the colormap
    img1_iso : ndarray
        Img1 colored using the isoluminant colormap generated
    new_rgb : ndarray
        Mixed image
    '''

    # Find J bounds to use on image (if possible)
    cmap_rgb, cmap_jab = get_rgb_jab(cmap)
    minJ, maxJ = find_J_bounds(cmap_jab, report=False)

    # Case 1: Colormap failed.
    if minJ is None:
        print('Colormap failed. Try a different one!')
        return None, None, None, None

    # Case 2: Colormap passed! Mixin' time!
    else:

        plot_3D_colormap(cmap_jab, minJ, maxJ, name=name,
                         maprevolve=maprevolve)

        # Initialize
        img1_rgb = np.zeros((img1.shape[0], img1.shape[1], 3), dtype=np.uint8)
        img1_jab = np.zeros((img1.shape[0], img1.shape[1], 2))
        img1_iso = np.zeros(img1_rgb.shape, dtype=np.uint8)
        new_rgb = np.zeros(img1_rgb.shape, dtype=np.uint8)

        # Save RGB & J'a'b' values corresponding to colormap
        for i in range(img1.shape[0]):
            for j in range(img1.shape[1]):
                value = int(round((img1[i, j] - low) * 255 / (high - low)))
                trgb = cmap_rgb[:, value]
                tjab = cmap_jab[:, value]
                img1_rgb[i, j, :] = [trgb[0] * 255, trgb[1] * 255,
                                     trgb[2] * 255]
                img1_jab[i, j, :] = [tjab[1], tjab[2]]

        # Combine a' & b' values of Img1 with J' of Img2
        j_values = _adjust_bounds(img2, minJ, maxJ)
        for i in range(img1.shape[0]):
            for j in range(img1.shape[1]):
                if img1[i, j] > low:
                    a = img1_jab[i, j, 0]
                    b = img1_jab[i, j, 1]
                    img1_iso[i, j, :] = convert([(maxJ + minJ) / 2, a, b],
                                                CSPACE2, CSPACE1) * 255
                    new_rgb[i, j, :] = convert([j_values[i, j], a, b],
                                               CSPACE2, CSPACE1) * 255

        return img1_rgb, img1_iso, new_rgb


def normalize(a):
    '''
    Normalize array so the average is at 0 and the std. dev. is 1.

    Parameters
    -----------
    a : array
        Array to be normalized

    Returns
    -----------
    new_array : array
        Normalized array. Same size as the original array.
    '''

    new_array = np.copy(a)
    return (new_array - np.average(new_array)) / np.std(new_array)


#%% Math Functions
def _find_distance(p1, p2):
    '''
    Finds the distance between two points. Must be the same length.
    '''

    if len(p1) != len(p2):
        return ValueError
    val = 0
    for i in range(len(p1)):
        val += (p2[i] - p1[i]) ** 2
    return sqrt(val)


def _rnt(num, shift='None'):
    '''
    Rounds number to the nearest 10 digit. Returned as int.
    '''
    if shift.lower() == 'upper':
        return int(ceil(num / 10.0) * 10)
    elif shift.lower() == 'lower':
        return int(floor(num / 10.0) * 10)
    else:
        return int(round(num / 10.0) * 10)


def _valid_rgb(num, e=0.001):
    '''
    Returns whether or not the number is both finite and between 0 and 1
    (within allowed error) to test whether it is valid RGB value.
    '''
    return np.isfinite(num) and num < (1 + e) and num > -e


#%% Plotting Functions
def _plot_3D(ax, m, rgb, lims, ticks):
    '''
    Plots J'a'b' values of colormap in 3D space. Points are colored
    with their corresponding RGB value.
    '''

    # Plot
    for i in range(m.shape[1]):
        c = tuple(rgb[:, i])
        ax.scatter(m[1, i], m[2, i], m[0, i], c=c, alpha=0.3, s=80, lw=0)

    # Format
    labels = ['J\'', 'a\'', 'b\'']
    ax.set_xlabel(labels[1], fontsize=FLABEL)
    ax.set_ylabel(labels[2], fontsize=FLABEL)
    ax.set_zlabel(labels[0], fontsize=FLABEL)
    ax.set_xlim(left=lims[0], right=lims[1])
    ax.set_ylim(bottom=lims[2], top=lims[3])
    ax.set_zlim(bottom=lims[4], top=lims[5])
    ax.set_xticks([ticks[0], ticks[1]])
    ax.set_yticks([ticks[2], ticks[3]])
    ax.set_zticks([ticks[4], ticks[5]])
    plt.xticks(fontsize=FAX)
    plt.yticks(fontsize=FAX)
    plt.axis('off')
    return


def plot_3D_colormap(jab, minJ, maxJ, name=None, maprevolve=False):
    '''
    Plots colormap, showing all available J'a'b' values through
    CAM02-UCS space.

    Parameters
    -------------
    jab : ndarray
        J'a'b' set generated from get_rgb_jab. J' values do not really
        matter.
    minJ : int
        Minimum J value found to work with all a'b' pairs
    maxJ : int
        Maximum J value found to work with all a'b' pairs
    name : string
        Name of file to be saved to. Make sure to include the file type
        (e.g. .png, .pdf). If name is None, the file will not be saved.
        Default value is None.
    maprevolve : boolean
        Decides whether full 3D rotation images will be plotted and
        saved for the 3D colormap plot. Extends total computation time
        about 10X. Is considered False is name is None. Default value
        is False.

    Returns
    -----------
    None.
    '''

    m = np.copy(jab)

    # Set Up
    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(111, projection='3d')
    topJ = _rnt(maxJ)
    botJ = _rnt(minJ)
    topa = _rnt(max(m[1, :]), shift='upper')
    bota = _rnt(min(m[1, :]), shift='lower')
    topb = _rnt(max(m[2, :]), shift='upper')
    botb = _rnt(min(m[2, :]), shift='lower')
    lims = [bota, topa, botb, topb, botJ, topJ]

    # Find RGBs for each possible J
    for J in range(minJ, maxJ + 1):
        m[0, :] = J
        rgb = np.zeros(m.shape)
        for col in range(m.shape[1]):
            rgb[:, col] = convert(m[:, col], CSPACE2, CSPACE1)
        _plot_3D(ax, m, rgb, lims, lims)

    # Plot and save rotating image
    if name is not None and maprevolve:
        for a in np.arange(0, 360, 30):
            ax.view_init(45, a)
            plt.draw()
            plt.savefig(name + 'angle=' + str(a) + '.png')
    plt.show()
    return


def plot_colormap(data, iso=False, ax=None):
    '''
    Plots the colorbar of a given colormap.

    Invalid colormap names throw a ValueError. Refer to
    _check_cmap for more information.

    Parameters
    -----------
    data: string OR 2-3D array
        Colormap name OR Colormap RGB values to use
    iso: boolean
        Whether or not to generate the isolum manp first. Default is
        False. Ignored if RGB values passed in directly.
    ax: matplotlib ax object (optional)
        Used for adding cmap as a subplot to larger plot. Default is to
        create a new plot.

    Returns
    -------
    '''

    # Colormap name passed in - get RGB values
    if type(data) == str:
        cmap = data
        _check_cmap(cmap)

        if iso:
            rgb = create_isoluminant_map(cmap)
        else:
            rgb, _ = get_rgb_jab(cmap)

    # RGB values passed in
    else:
        rgb = data

    if rgb is None:
        return None

    # Create plot
    newfig = ax == None
    if newfig:
        plt.figure(figsize=(6, 6))
        ax = plt.subplot(111)

    # RGB values generated, now plot
    if len(rgb.shape) == 2:
        for i in range(rgb.shape[1]):
            c = tuple(rgb[:, i])
            plt.scatter([i] * 100, np.linspace(0, 10, 100), c=c, lw=0)
    else:
        k = 10.0 / rgb.shape[2]
        y = max(50 / rgb.shape[2], 5)
        for j in range(rgb.shape[2]):
            for i in range(rgb.shape[1]):
                c = tuple(rgb[:, i, j])
                plt.scatter([i] * y, np.linspace(k * j, k * (j + 1), y), c=c, lw=0)

    # Final formatting
    ax.set_aspect(5)
    plt.axis([0, rgb.shape[1], 0, 10])
    plt.axis('off')

    return rgb


def plot_colormap_info(fig, data, sp=[5, 1, 1], name=None, show=True, leg=False):
    '''
    Takes in the name of a colormap and plots its colorbar, distance
    between each point on the map, and its 3D J'a'b' map with each
    point colored with its corresponding RGB value.

    Invalid colormap names throw a ValueError. Refer to
    _check_cmap for more information.

    Parameters
    -----------
    cmap: string
        Colormap name
    name : string
        Name of file to be saved to. Make sure to include the file type
        (e.g. .png, .pdf). If name is None, the file will not be saved.
        Default value is None.

    Returns
    -----------
    None.
    '''

    rgb, m = get_rgb_jab(data)

    # Set up for figure
    if fig is None:
        fig = plt.figure(figsize=(6, 12))

    # Show colorbar
    ax = plt.subplot(sp[0], sp[1], sp[2])
    plot_colormap(rgb, ax=ax)

    # Show colorbar test
    ax = plt.subplot(sp[0], sp[1], sp[2] + sp[1])
    plt.imshow(test_colormap(rgb, ax=ax))
    plt.axis('off')
    ax.set_aspect(1.2)

    # 2D Plot - J'a'b' values
    ax = fig.add_subplot(sp[0], sp[1], sp[2] + sp[1] * 2)
    _plot_jab(m, leg=leg)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 2D Plot - Distance Between Points (Perceptual Deltas)
    ax = fig.add_subplot(sp[0], sp[1], sp[2] + sp[1] * 3)
    _plot_pd(m)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 3D Plot - Colormap Representation in CAM02-UCS
    ax = fig.add_subplot(sp[0], sp[1], sp[2] +  + sp[1] * 4, projection='3d')
    lims = [-32.3, 41.6, -39.3, 35.7, 0, 100]
    ticks = [-30, 30, -30, 30, 0, 100]
    _plot_3D(ax, m, rgb, lims, ticks)

    # Save figure
    if name is not None:
        plt.savefig(name, transparent=True)
    if show:
        plt.show()
    return


def _plot_jab(m, leg=False):
    '''
    Plots J'a'b' values
    '''
#    plt.title('CAM02-UCS Colorspace', fontsize=FLABEL)
    c1 = (45 / 255.0, 145 / 255.0, 167 / 255.0, 1)
    c2 = (220 / 255.0, 41 / 255.0, 12 / 255.0, 1)
    j, = plt.plot(m[0, :], 'k', lw=3, label='J\'')
    a, = plt.plot(m[1, :], c=c1, lw=3, label='a\'')
    b, = plt.plot(m[2, :], c=c2, lw=3, label='b\'')
    plt.tick_params(which='both', left='off', right='off')
    plt.xticks([])
    plt.yticks([-40, 0, 40, 80], fontsize=FAX)
    plt.axis([0, m.shape[1], -40, 100])

    if leg:
        plt.legend(handles=[j, a, b], loc='upper left', fontsize=FAX)

    return


def _plot_pd(m, show=True):
    '''
    Plots perceptual deltas as shown in https://bids.github.io/colormap
    '''
#    plt.title('Perceptual Deltas', fontsize=FLABEL)
    d = np.zeros(m.shape[1] - 1)
    for i in range(m.shape[1] - 1):
        d[i] = _find_distance(m[:, i], m[:, i+1])

    if show:
        ymax = max(3, np.max(d))
        plt.xlim(left=1, right=m.shape[1]-1)
        plt.ylim(bottom=0, top=ymax)
        plt.xticks([])
        plt.yticks([0, floor(ymax)], fontsize=FAX)
        plt.plot(d, 'k', lw=3)
        plt.tick_params(which='both', bottom='off', right='off', top='off')
#    plt.ylabel('Dist. to Next Pt.', fontsize=FLABEL)
#    plt.axis('off')
    return d


def plot_linear_Js(low, high, j1, j2, name=None):
    plt.figure(figsize=(6, 6))
    c1 = (99 / 255.0, 198 / 255.0, 10 / 255.0)
    c2 = (184 / 255.0, 156 / 255.0, 239 / 255.0)
    plt.plot(high, 'k', lw=4)
    plt.plot(low, 'k', lw=4)
    if j1 is not None:
        plt.plot(j1[0, :], c='k', lw=4.8)
        plt.plot(j1[0, :], c=c1, lw=4)
    if j2 is not None:
        plt.plot(j2[0, :], 'k', lw=4.8)
        plt.plot(j2[0, :], c=c2, lw=4)
    plt.axis([0, 256, 0, 100])
    plt.xticks([])
    plt.yticks([0, 50, 100], fontsize=FAX)
    plt.ylabel('J\'', fontsize=FLABEL)
    plt.title('J\' Fits Used', fontsize=FLABEL)
    p1 = mpatches.Patch(color='k', label='Bounds')
    p2 = mpatches.Patch(color=c1, label='Fit to Original')
    p3 = mpatches.Patch(color=c2, label='Maximize Range')
    patches = [p1, p2, p3]
    plt.legend(handles=patches, loc='lower right', fontsize=FAX)
    if name is not None:
        plt.savefig(name, dpi=300)
    plt.show()


def _correct_J(low, high, line, m):
    test_upper = [x for x in high - line if x < 0]
    test_lower = [x for x in line - low if x < 0]
    if len(test_upper) + len(test_lower) == 0:
        m = np.copy(m)
        m[0, :] = line
        return m
    else:
        return None


def lin_fit(y):
    x = range(256)
    x = np.vstack([x, np.ones(len(x))]).T
    a, _, _, _ = np.linalg.lstsq(x, y)
    return (a * x)[:, 0]


def correct_J(m, name=None, delta_slope=1, delta_b=1):

    # Get max and min boundaries for each a, b pair
    l = m.shape[1]
    high = np.zeros((l))
    low = np.zeros((l))
    for i in range(l):
        l, h = find_J_bounds(m[:, i], report=False)
        low[i], high[i] = l, h

    # Method 1: Fit to existing line
    m1 = np.copy(m)
    slope, b = np.polyfit(range(256), m[0, :], 1)
    line_fit = slope * np.copy(range(256)) + b
    if max(line_fit) > 99:
        temp = list(m[0, :] - 99)
        line_fit = lin_fit(temp) + (99 - np.max(lin_fit(temp)))
        if min(line_fit) < 1:
            if line_fit[0] < line_fit[-1]:
                line_fit = np.linspace(1, 99, 256)
            else:
                line_fit = np.linspace(99, 1, 256)
    m1[0, :] = line_fit

    # Method 2: Maximize change in J
    m2 = None
#    if [x for x in (high - min(low)) if x < 0]
    if m[0, 0] <= m[0, -1]:
        delta_slope = -abs(delta_slope)
        slope = high[-1] - low[0]
        if slope < 0:
            plot_linear_Js(low, high, m1, None, name=name)
            return m1, None
    else:
        delta_slope = abs(delta_slope)
        slope = low[-1] - high[0]
        if slope > 0:
            plot_linear_Js(low, high, m1, None, name=name)
            return m1, None

    max_b = max(high[0], high[-1])
    while slope != 0:
        b = low[0]
        while b <= max_b:
            line_fit = (slope / 256.0) * np.asarray(range(256)) + b
#            plot_linear_Js(low, high, m1, m2)
#            test_upper = [x for x in high - line_fit2 if x < 0]
#            test_lower = [x for x in line_fit2 - low if x < 0]
#            if len(test_upper) + len(test_lower) == 0:
#                plot_linear_Js(low, high, line_fit1, line_fit2, name=name)
#                m2 = np.copy(m)
#                m2[0, :] = line_fit2
#                return m1, m2
            m2 = _correct_J(low, high, line_fit, m)
            if m2 is not None:
                plot_linear_Js(low, high, m1, m2, name=name)
                return m1, m2
            elif line_fit[-1] > high[-1] or line_fit[0] > high[0]:
                b = 100
            else:
                b += delta_b
        slope += delta_slope
    plot_linear_Js(low, high, m1, None, name=name)
    return m1, None


# Make jab perceptually uniform
def make_linear(jab, l=10000):

    jab = np.copy(jab)

    # Interpolate
    old_x = range(256)
    new_x = np.linspace(0, 255, l)
    long_a = np.interp(new_x, old_x, jab[1, :])
    long_b = np.interp(new_x, old_x, jab[2, :])

    total_length = 0
    for i in range(1, l):
        total_length += _find_distance([long_a[i - 1], long_b[i - 1]],
                                       [long_a[i], long_b[i]])
    d = total_length / 255 # Desired distance between points

    # Modify a & b
    jab_ind = 0
    long_ind = 1
    d_this = 0
    while jab_ind < 254 and long_ind < l - 1:
        test_d1 = _find_distance([long_a[long_ind - 1], long_b[long_ind - 1]],
                                [long_a[long_ind], long_b[long_ind]])
        test_d2 = _find_distance([long_a[long_ind], long_b[long_ind]],
                                [long_a[long_ind + 1], long_b[long_ind + 1]])

        d_this += test_d1
        d_next = d_this + test_d2
        # If the distance to this point is a minima, add. Else, move onto next
        if abs(d * (jab_ind + 1) - d_this) < abs(d *  (jab_ind + 1) - d_next):
            jab_ind += 1
            jab[1, jab_ind] = long_a[long_ind]
            jab[2, jab_ind] = long_b[long_ind]
        long_ind += 1

    return jab


def overlay_colormap(img, cmap_rgb, ax=None, name=None, plot_ready=True):
#    newfig = ax == None
#    if newfig:
#        plt.figure(figsize=(8, 4))
#        ax = plt.subplot(1, 1, 1)
    img = np.copy(img)
    if plot_ready:
        img_rgb = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
    else:
        img_rgb = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.float16)
    max_val = cmap_rgb.shape[1]
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            value = int(round(((img[i, j] - np.min(img)) * (max_val - 1)) / (np.max(img) - np.min(img))))
            trgb = cmap_rgb[:, value]
            if plot_ready:
                img_rgb[i, j, :] = [trgb[0] * 255, trgb[1] * 255, trgb[2] * 255]
            else:
                img_rgb[i, j, :] = [trgb[0], trgb[1], trgb[2]]
#    if newfig:
#        plt.imshow(img_rgb)
#        plt.axis('off')
#        ax.set_aspect(1.2)

    return img_rgb


def test_colormap(cmap, ax=None, name=None):
    sin_mag = 8.0
    rgb, _ = get_rgb_jab(cmap)
    h = 45
    w = 256
    x = range(w)
    img = np.zeros((h, w))

    for i in range(h):
        img[i, :] = (sin_mag - sin_mag * i / h) * np.sin(x) + x
    img = normalize(img)
    img_rgb = overlay_colormap(img, rgb, ax=ax, name=name)
    return img_rgb


def cdps_plot(img, cmap, rgb, num, gslope):

    plt.figure(figsize=(4, 4))

    img_overlay = overlay_colormap(img, rgb, plot_ready=False)[0, :, :]
    slice_jab = convert(img_overlay.T, CSPACE1, CSPACE2)

    overlay_pd = _plot_pd(slice_jab, show=False)

    data_pd = np.zeros(img_overlay.shape[0] - 1)
    for i in range(data_pd.shape[0]):
        data_pd[i] = img[0, i + 1] - img[0, i]

    # Get x and y
    x = abs(data_pd)
    y = overlay_pd / gslope

    # R^2
    coeffs = np.polyfit(x, y, 1)
    coeffs[1] = 0
    p = np.poly1d(coeffs)
    yhat = p(x)
    ybar = np.sum(y)/len(y)
    ssreg = np.sum((yhat-ybar)**2)
    sstot = np.sum((y - ybar)**2)

    # Plot fitted line
    plt.plot(x, yhat, 'gray', lw=2, zorder=-32)
    plt.scatter(x, y, c='k', s=40, zorder=32)

    # Final formatting
    plt.xticks([])
    plt.yticks([])
    plt.axis([0, 1, 0, 2])
    plt.title('y = %.2fx + %.2f, R2 = %.3f' % (coeffs[0], coeffs[1], ssreg / sstot))
    plt.show()
