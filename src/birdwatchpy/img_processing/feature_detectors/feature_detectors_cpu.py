import cv2 as cv
import numpy as np


class GoodFeaturesToTrackCPU:
    def __init__(self, maxCorners=150, qualityLevel=0.03, minDistance=5, blockSize=50):
        self.maxCorners = maxCorners
        self.qualityLevel = qualityLevel
        self.minDistance = minDistance
        self.blockSize = blockSize

    def detect(self, img_gray: np.ndarray):
        return cv.goodFeaturesToTrack(img_gray, self.maxCorners, self.qualityLevel, self.minDistance,
                                      self.blockSize)
