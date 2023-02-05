import cv2 as cv
import numpy as np


class GoodFeaturesToTrackGPUNaive_create:
    def __init__(self, max_corners, quality_level, min_distance, block_size):
        self.max_corners = max_corners
        self.quality_level = quality_level
        self.min_distance = min_distance
        self.block_size = block_size

        self.detector_device = cv.cuda.createGoodFeaturesToTrackDetector(cv.CV_8UC1, max_corners,
                                                                         quality_level,
                                                                         min_distance,
                                                                         block_size)

        self.p_device = cv.cuda_GpuMat()
        self.gray_device = cv.cuda_GpuMat()

    def detect(self, img_gray: np.ndarray):
        self.gray_device = cv.cuda_GpuMat(img_gray)
        self.p_device = self.detector_device.detect(self.gray_device)
        return self.p_device.download()
