import numpy as np
from matplotlib import pyplot as plt

BINS = np.arange(0.0, 6.0, 0.06)


def get_histogram_data(array):
    hist, bins = np.histogram(array.flatten(), bins=BINS)
    return hist


def show_histogram(array):
    # print(np.bincount(array.flatten()))
    plt.hist(array.flatten(), bins=BINS)
    plt.title("histogram")
    plt.show()


def save_histogram(array, path):
    # print(np.bincount(array.flatten()))
    plt.hist(array.flatten(), bins=BINS)
    plt.title("histogram")
    plt.savefig(f'{path}/histogram.png')
