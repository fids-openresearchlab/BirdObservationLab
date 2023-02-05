#!/usr/bin/env python
import time
from pathlib import Path

import cv2 as cv
import numpy as np

from birdwatchpy.frames.FrameData import FrameData
from birdwatchpy.img_processing.feature_detectors.feature_detectors_cpu import GoodFeaturesToTrackCPU
from birdwatchpy.optical_flow.sparse.SparseOpticalFlowData import SparseOpticalFlowData


class LucasKanadeCPU:
    def __init__(self, params):
        self.params = params

        if params["feature_detector"]["name"] == 'fast':
            self.feature_detector = cv.FastFeatureDetector_create()
        elif params["feature_detector"]["name"] == 'goodFeaturesToTrack':
            self.feature_detector = GoodFeaturesToTrackCPU(**params["feature_detector"]["feature_params"])
        else:
            print(params["feature_detector"])
            print(params["feature_detector"]["name"])

    def calc(self, frame0: FrameData, frame1: FrameData):
        if frame0.img_grey is None:
            frame0.img_grey = cv.cvtColor(frame0.img_rgb.copy(), cv.COLOR_BGR2GRAY)
        if frame1.img_grey is None:
            frame1.img_grey = cv.cvtColor(frame1.img_rgb.copy(), cv.COLOR_BGR2GRAY)

        p0 = self.feature_detector.detect(frame0.img_grey)
        if isinstance(p0[0],
                      cv.KeyPoint):  # ToDo: Check if opencv sparse opt flow can also handle keyboints. If yes remove
            p0 = [kp.pt for kp in p0]

        p0 = np.float32(p0)  # .reshape(-1, 2)

        if False:
            instance = cv.optflow.RLOFOpticalFlowParameter_create()
            p1, st, err = cv.optflow.calcOpticalFlowSparseRLOF(
                frame0.img_rgb,
                frame1.img_rgb,
                p0, None, rlofParam=instance,
                forwardBackwardThreshold=1)

            good_new = p1[st]
            good_old = p0[st]

        if True:
            p1, st, err = cv.calcOpticalFlowPyrLK(frame0.img_grey, frame1.img_grey, p0, None,
                                                  **self.params["lk_params"])
            p0r, st, err = cv.calcOpticalFlowPyrLK(frame1.img_grey, frame0.img_grey, p1, None,
                                                   **self.params["lk_params"])

            d = abs(p0 - p0r).reshape(-1, 2).max(-1)
            good = d < 1

            # Select good points
            good_new = p1[good]
            good_old = p0[good]

        if good_new.size ==0 or good_old.size==0:
            return

        if False:  # ToDo: Remove if not used for debugging
            # draw the tracks
            mask = np.zeros_like(frame0.img_rgb)
            for i, (new, old) in enumerate(zip(good_new, good_old)):
                # print(new.astype(int).ravel())
                # print(old.astype(int).ravel())
                a, b = new.astype(int).ravel()
                c, d = old.astype(int).ravel()
                mask = cv.line(mask, (a, b), (c, d), [0, 255, 0], 2)
                feature_frame0 = cv.circle(frame0.img_rgb, (c, d), 5, [255, 0, 5], -1)
                feature_frame1 = cv.circle(frame1.img_rgb, (a, b), 5, [255, 0, 5], -1)

            frame0.img_rgb = cv.add(frame0.img_rgb, mask)
            frame1.img_rgb = cv.add(frame1.img_rgb, mask)

            cv.imwrite(f"{frame0.frame_number}_cpu_result.png", frame0.img_rgb)
            cv.imwrite(f"{frame1.frame_number}_cpu_result.png", frame1.img_rgb)

        #print(np.concatenate(good_old, good_new))
        #res = np.linalg.norm(good_old - good_old)
        #print("Distance!", flush=True)
        #print(res.shape)
        #print(res)


        #print(good_old, flush=True)

        #print(np.max(scipy.spatial.distance.cdist(good_old.reshape((-1,2)),good_new.reshape((-1,2)), 'euclidean')))
        #print(np.linalg.norm(good_old.reshape((-1,2))-good_new.reshape((-1,2))))
        max_n =np.max(np.hypot(*(good_old.reshape((-1,2)) - good_new.reshape((-1,2))).T))
        max =0
        #is_relevant=False
        #for f1, f0 in zip(good_new, good_old):
        #    x_new, y_new = f1.astype(int).ravel()
        #    x_old, y_old = f0.astype(int).ravel()
        #    dist = float(np.linalg.norm(f0 - f1))
        #    frame1.sparse_opt_flow.append(SparseOpticalFlowData(x_old, y_old, x_new, y_new, dist))
        #    if float(dist) > max:
        #        max = float(dist)
        #    if float(dist) > 4:  # ToDo: Remove!
        #        is_relevant=True  # ToDo: Remove!
        #        frame1.sparse_opt_flow.append(SparseOpticalFlowData(x_old, y_old, x_new, y_new, dist))
        #print(max)
        #print(max_n)
        #assert(int(max) ==int(max_n))
        #print(f'may {max}')

        if max_n>4:
            return frame1
        else:
            return None


class LucasKanadeGPU:
    def __init__(self, params):
        self.lk_params = params

        self.frame0: np.ndarray = None
        self.frame1: np.ndarray = None

        self.p0_device = None
        self.p1_device = None

        self.frame0_gray_device = None
        self.frame1_gray_device = None

        self.detector_device = None
        self.opt_flow = cv.cuda.SparsePyrLKOpticalFlow_create(params["lk_params"]["winSize"],
                                                              maxLevel=params["lk_params"]["maxLevel"])
        self.opt_flow.setNumIters(10)

        if params["feature_detector"]["name"] == 'fast':
            pass  # ToDo: Implement
        elif params["feature_detector"]["name"] == 'goodFeaturesToTrack':
            self.detector_device = cv.cuda.createGoodFeaturesToTrackDetector(cv.CV_8UC1, **params["feature_detector"][
                "feature_params"])

    def initiate_devices(self):
        self.frame0_gray_device = cv.cuda_GpuMat(self.frame0.img_grey)
        self.frame1_gray_device = cv.cuda_GpuMat(self.frame1.img_grey)

    def calc(self, frame0: FrameData, frame1: FrameData):
        start = time.time()
        if frame0.img_grey is None:
            self.frame0 = frame0
            self.frame0.img_grey = cv.cvtColor(frame0.img_rgb.copy(), cv.COLOR_BGR2GRAY)  # ToDo: Move conversion to GPU
        if frame1.img_grey is None:
            self.frame1 = frame1
            self.frame1.img_grey = cv.cvtColor(frame1.img_rgb.copy(), cv.COLOR_BGR2GRAY)  # ToDo: Move conversion to GPU

        if self.p0_device is None:
            self.initiate_devices()
        else:
            self.frame0_gray_device.upload(self.frame0.img_grey)
            self.frame1_gray_device.upload(self.frame1.img_grey)

        # Detect new features
        self.p0_device = self.detector_device.detect(self.frame0_gray_device)

        # calculate optical flow
        self.p1_device, st_device, err = self.opt_flow.calc(self.frame0_gray_device, self.frame1_gray_device,
                                                            self.p0_device, None)
        self.p0r_device, st_device, err = self.opt_flow.calc(self.frame1_gray_device, self.frame0_gray_device,
                                                             self.p1_device, None)

        # dload points
        p1 = self.p1_device.download()
        p0 = self.p0_device.download()
        p0r = self.p0r_device.download()

        d = abs(p0 - p0r).reshape(-1, 2).max(-1)
        good = d < 1

        # Select good points
        good_new = p1[0][good]
        good_old = p0[0][good]

        print(f'Took {time.time() - start}')

        if False:  # ToDo: Remove if not used for debugging
            # draw the tracks
            mask = np.zeros_like(frame0.img_rgb)
            for i, (new, old) in enumerate(zip(good_new, good_old)):
                # print(new.astype(int).ravel())
                # print(old.astype(int).ravel())
                a, b = new.astype(int).ravel()
                c, d = old.astype(int).ravel()
                mask = cv.line(mask, (a, b), (c, d), [0, 255, 0], 2)
                feature_frame0 = cv.circle(frame0.img_rgb, (c, d), 5, [255, 0, 5], -1)
                feature_frame1 = cv.circle(frame1.img_rgb, (a, b), 5, [255, 0, 5], -1)

            frame0.img_rgb = cv.add(frame0.img_rgb, mask)
            frame1.img_rgb = cv.add(frame1.img_rgb, mask)

            cv.imwrite(f"{frame0.frame_number}_result.png", frame0.img_rgb)
            cv.imwrite(f"{frame1.frame_number}_result.png", frame1.img_rgb)

        for f1, f0 in zip(good_new, good_old):
            x_new, y_new = f1.astype(int).ravel()
            x_old, y_old = f0.astype(int).ravel()
            dist = int(np.linalg.norm(f0 - f1))
            frame1.sparse_opt_flow.append(SparseOpticalFlowData(x_old, y_old, x_new, y_new, dist))

        print(f'Till end Took {time.time() - start}')
        return frame1


if __name__ == "__main__":
    print(Path("../000066.jpg").is_file())
    print(Path("../000068.jpg").is_file())

    params = {
        "feature_detector": {
            # Parameters for Shi-Tomasi corner detection
            "name": "goodFeaturesToTrack",
            "feature_params": {
                "maxCorners": 150,
                "qualityLevel": 0.03,
                "minDistance": 5,
                "blockSize": 50
            },
        },
        # Parameters for Lucas-Kanade optical flow
        "lk_params": {
            "winSize": [50, 50],
            "maxLevel": 6,
            "criteria": (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)}
    }

    gpu_opt_flow = LucasKanadeGPU(params)

    frame0 = FrameData(session_id=1, frame_number=66, img_rgb=cv.imread("../000066.jpg"))
    frame1 = FrameData(session_id=1, frame_number=68, img_rgb=cv.imread("../000068.jpg"))
    gpu_opt_flow.calc(frame0, frame1)

    frame0 = FrameData(session_id=1, frame_number=22, img_rgb=cv.imread("../000022.jpg"))
    frame1 = FrameData(session_id=1, frame_number=25, img_rgb=cv.imread("../000025.jpg"))
    gpu_opt_flow.calc(frame0, frame1)

    cpu_opt_flow = LucasKanadeCPU(params)

    frame0 = FrameData(session_id=1, frame_number=66, img_rgb=cv.imread("../000066.jpg"))
    frame1 = FrameData(session_id=1, frame_number=68, img_rgb=cv.imread("../000068.jpg"))
    cpu_opt_flow.calc(frame0, frame1)

    frame0 = FrameData(session_id=1, frame_number=22, img_rgb=cv.imread("../000022.jpg"))
    frame1 = FrameData(session_id=1, frame_number=25, img_rgb=cv.imread("../000025.jpg"))
    cpu_opt_flow.calc(frame0, frame1)

    if False:
        lk = LucasKanadeCPU(lk_params)
        prev_frame = None
        for frame in VideoLoader(video_path=Path(
                "/home/jo/coding_projects/fids_bird_detection_and_tracking/local_data/example/1631281579072_0008402_0008462.avi")):
            if prev_frame is None:
                prev_frame = frame
                continue
            else:
                # print(prev_frame.shape)
                # print(frame.shape)
                lk.calc(prev_frame, frame)
                prev_frame = frame
