import matplotlib.pyplot as plt
import numpy as np


def compass(angles, radii, title: str, show_direction_labels:bool=False, arrowprops=None):
    """
    Compass draws a graph that displays the vectors with
    components `u` and `v` as arrows from the origin.
    """

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))

    kw = dict(arrowstyle="->", color='k')
    if arrowprops:
        kw.update(arrowprops)

    [ax.annotate("", xy=(angle, radius), xytext=(0, 0), arrowprops=kw) for angle, radius in zip(angles, radii)]
    ax.set_ylim(0, np.max(radii))
    ax.set_title(title, pad=20)
    if show_direction_labels:
        ax.set_xticklabels(['N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NO'])

    return fig, ax
