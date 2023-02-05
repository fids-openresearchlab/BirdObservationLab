#!/usr/bin/env python
from pathlib import Path

import cv2
import numpy as np

from birdwatchpy.Generators.VideoLoader import VideoLoader
from birdwatchpy.frames.FrameData import FrameData
from birdwatchpy.optical_flow.sparse.SparseOpticalFlowData import SparseOpticalFlowData

params = {
    # Parameters for Shi-Tomasi corner detection
    "feature_params": {
        "max_corners": 150,
        "quality_level": 0.03,
        "min_distance": 5,
        "block_size": 50
    },
    # Parameters for Lucas-Kanade optical flow
    "lk_params": {
        "winSize": [50, 50],
        "maxLevel": 6,
        "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)}
}

feature_params = params["feature_params"]
lk_params = params["lk_params"]


class LucasKanadeCPU:
    def __init__(self, params):
        self.lk_params = params
        self.feature_detector = feature_detector

    def calc(self, frame0: FrameData, frame1: FrameData):
        if frame0.img_grey is None:
            frame0.img_grey = cv2.cvtColor(frame0.img_rgb.copy(), cv2.COLOR_BGR2GRAY)
        if frame1.img_grey is None:
            frame1.img_grey = cv2.cvtColor(frame1.img_rgb.copy(), cv2.COLOR_BGR2GRAY)

        p0 = self.feature_detector.detect(frame0.img_grey)
        # if isinstance(p0[0], cv2.KeyPoint): # ToDo: Check if opencv sparse opt flow can also handle keyboints. If yes remove
        #    p0 = [kp.pt for kp in p0]

        p0 = np.float32(p0)  # .reshape(-1, 2)

        if False:
            instance = cv2.optflow.RLOFOpticalFlowParameter_create()
            p1, st, err = cv2.optflow.calcOpticalFlowSparseRLOF(
                frame0.img_rgb,
                frame1.img_rgb,
                p0, None, rlofParam=instance,
                forwardBackwardThreshold=1)

            good_new = p1[st]
            good_old = p0[st]

        if True:
            p1, st, err = cv2.calcOpticalFlowPyrLK(frame0.img_grey, frame1.img_grey, p0, None, **lk_params)
            p0r, st, err = cv2.calcOpticalFlowPyrLK(frame1.img_grey, frame0.img_grey, p1, None, **lk_params)

            d = abs(p0 - p0r).reshape(-1, 2).max(-1)
            good = d < 1

            # Select good points
            good_new = p1[good]
            good_old = p0[good]

        if False:  # ToDo: Remove if not used for debugging
            # draw the tracks
            mask = np.zeros_like(frame0.img_grey)
            for i, (new, old) in enumerate(zip(good_new, good_old)):
                print(new.astype(int).ravel())
                print(old.astype(int).ravel())
                a, b = new.astype(int).ravel()
                c, d = old.astype(int).ravel()
                mask = cv2.line(mask, (a, b), (c, d), [255, 100, 100], 2)
                frame = cv2.circle(frame1.img_grey, (a, b), 5, [255, 0, 5], -1)

                img = cv2.add(frame, mask)

                cv2.imshow('frame', img)
                k = cv2.waitKey(30) & 0xff

        for f1, f0 in zip(good_new, good_old):
            x_new, y_new = f1.astype(int).ravel()
            x_old, y_old = f0.astype(int).ravel()
            dist = int(np.linalg.norm(f0 - f1))
            frame1.sparse_opt_flow.append(SparseOpticalFlowData(x_old, y_old, x_new, y_new, dist))

        return frame1


class LucasKanadeTrackerCPU:
    def __init__(self, params):
        self.track_len = 2
        self.detect_interval = 5
        self.tracks = []
        self.frame_idx = 0
        self.lk_params = params
        self.frame_gray = None

    def calc(self, new_gray_frame: np.ndarray):
        vis = new_gray_frame.copy()
        self.frame_gray = new_gray_frame
        img0, img1 = self.prev_gray, self.frame_gray

        assert (len(img1.shape) == 2)

        p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)

        p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **self.lk_params)
        p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **self.lk_params)
        print("after sparse calc")
        d = abs(p0 - p0r).reshape(-1, 2).max(-1)
        good = d < 1
        new_tracks = []
        for tr, (x, y), good_flag in zip(self.tracks, p1.reshape(-1, 2), good):
            if not good_flag:
                continue
            tr.append((x, y))
            if len(tr) > self.track_len:
                del tr[0]
            new_tracks.append(tr)
            cv2.circle(vis, (int(x), int(y)), 2, (0, 255, 0), -1)
        print("self.tracks becomes new tracks")
        print(self.tracks)
        print(f"new_tracks: {new_tracks}")
        self.tracks = new_tracks
        # if len(self.tracks) > 30: # ToDo: Added by me. Should it be done different?
        #    self.tracks = self.tracks[-30:]

        # if self.frame_idx % self.detect_interval == 0:
        #    mask = np.zeros_like(frame_gray)
        #    mask[:] = 255
        #    for x, y in [np.int32(tr[-1]) for tr in self.tracks]:
        #        cv2.circle(mask, (x, y), 5, 0, -1)
        #    p = cv2.goodFeaturesToTrack(frame_gray, mask = mask, **feature_params)
        #    if p is not None:
        #        for x, y in np.float32(p).reshape(-1, 2):
        #            self.tracks.append([(x, y)])

        # self.frame_idx += 1
        self.prev_gray = self.frame_gray

        # cv2.imshow('lk_track', vis)
        # ch = cv2.waitKey(10)

        return [np.int32(tr) for tr in self.tracks]


if __name__ == "__main__":
    lk = LucasKanadeCPU(lk_params)
    prev_frame = None
    for frame in VideoLoader(video_path=Path(
            "//local_data/example/1631281579072_0008402_0008462.avi")):
        if prev_frame is None:
            prev_frame = frame
            continue
        else:
            # print(prev_frame.shape)
            # print(frame.shape)
            lk.calc(prev_frame, frame)
            prev_frame = frame
