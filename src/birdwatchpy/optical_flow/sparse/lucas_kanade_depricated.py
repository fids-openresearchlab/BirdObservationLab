import time

import cv2
import numpy as np


def gpu_v2(vid_path: str, parames: dict):
    feature_params = parames["feature_params"]
    lk_params = parames["lk_params"]

    # The video feed is read in as a VideoCapture object
    cap = cv2.VideoCapture(vid_path)

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    out = cv2.VideoWriter(f'{parames["name"]}.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 26,
                          (frame_width, frame_height))

    # Variable for color to draw optical flow track
    color = (0, 255, 0)
    # Take first frame and find corners in it
    ret, old_frame = cap.read()
    old_gray_device = cv2.cuda_GpuMat(cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY))
    detector_device = cv2.cuda.createGoodFeaturesToTrackDetector(cv2.CV_8UC1, feature_params['maxCorners'],
                                                                 feature_params['qualityLevel'],
                                                                 feature_params['minDistance'],
                                                                 feature_params['blockSize'])

    p0_device = detector_device.detect(old_gray_device)
    p1_device = detector_device.detect(old_gray_device)

    optFlow = cv2.cuda_SparsePyrLKOpticalFlow.create(lk_params["winSize"], lk_params["maxLevel"], iters=10)

    frame_gray_device = cv2.cuda_GpuMat()

    start = time.time()
    counter = 0
    while True:
        ret, frame = cap.read()
        if frame is None:
            break
        frame_gray_device.upload(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

        # Detect new features
        p0_device = detector_device.detect(old_gray_device)

        # calculate optical flow
        p1_device, st_device, err = optFlow.calc(old_gray_device, frame_gray_device, p0_device, None)

        # dload points
        p1 = p1_device.download()
        p0 = p0_device.download()
        st = st_device.download()

        if p1 is None:
            frame_gray_device.copyTo(old_gray_device)
            continue

        # assert(st.shape[1]==p0.shape[1])
        # assert(p1.shape[1]==p0.shape[1])

        # Select good points
        good_new = p1[st == 1]
        good_old = p0[st == 1]

        # draw_and_show(good_old,good_new, frame)
        # frame = simple_lines_draw(good_old, good_new, frame)

        # cv2.imshow('frame', frame)
        # k = cv2.waitKey(2) & 0xff
        # if k == 27:
        #    break

        out.write(frame)

        # Now update the previous frame
        frame_gray_device.copyTo(old_gray_device)

        # Now update the previous points and adjust point array dimension
        # p0 = np.expand_dims(good_new,axis=0).astype(np.int16)
        # po_device.upload(p0)

    cap.release()
    out.release()


def calc_lucas_kanade_optical_flow(parames: dict):
    feature_params = parames["feature_params"]
    lk_params = parames["lk_params"]

    prev = None

    # Variable for color to draw optical flow track
    color = (0, 255, 0)

    while True:
        next_frame = yield

        if prev is None:
            # Converts frame to grayscale because we only need the luminance channel for detecting edges - less computationally expensive
            prev_gray = cv.cvtColor(next_frame, cv.COLOR_BGR2GRAY)
            # Finds the strongest corners in the first frame by Shi-Tomasi method - we will track the optical flow for these corners
            # https://docs.opencv.org/3.0-beta/modules/imgproc/doc/feature_detection.html#goodfeaturestotrack
            prev = cv.goodFeaturesToTrack(prev_gray, mask=None, **feature_params)

            # Creates an image filled with zero intensities with the same dimensions as the frame - for later drawing purposes
            mask = np.zeros_like(next_frame)

            yield None
            next_frame = yield

        # Converts each frame to grayscale - we previously only converted the first frame to grayscale
        gray = cv.cvtColor(next_frame, cv.COLOR_BGR2GRAY)
        # Calculates sparse optical flow by Lucas-Kanade method
        # https://docs.opencv.org/3.0-beta/modules/video/doc/motion_analysis_and_object_tracking.html#calcopticalflowpyrlk
        prev = cv.goodFeaturesToTrack(prev_gray, mask=None, **feature_params)
        next, status, error = cv.calcOpticalFlowPyrLK(prev_gray, gray, prev, None, **lk_params)
        # Selects good feature points for previous position
        good_old = prev[status == 1].astype(int)
        # Selects good feature points for next position
        good_new = next[status == 1].astype(int)
        # Draws the optical flow tracks
        for i, (new, old) in enumerate(zip(good_new, good_old)):
            # Returns a contiguous flattened array as (x, y) coordinates for new point
            a, b = new.ravel()
            # Returns a contiguous flattened array as (x, y) coordinates for old point
            c, d = old.ravel()
            # Draws line between new and old position with green color and 2 thickness
            # mask = cv.line(mask, (a, b), (c, d), color, 2)
            # Draws filled circle (thickness of -1) at new position with green color and radius of 3
            # frame = cv.circle(frame, (a, b), 3, color, -1)
            frame = cv.line(frame, (a, b), (c, d), color, 2)
        # Overlays the optical flow tracks on the original frame
        output = cv.add(frame, mask)
        # Updates previous frame
        prev_gray = gray.copy()
        # Updates previous good feature points
        print(good_new)
        prev = good_new.reshape(-1, 1, 2)
        print(prev)
        # Opens a new window and displays the output frame
        cv.imshow("sparse optical flow", output)

        yield good_new, good_old

        # Frames are read by intervals of 10 milliseconds. The programs breaks out of the while loop when the user presses the 'q' key
        if cv.waitKey(10) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    parameter_list = [
        {
            "name": "4",
            # Parameters for Shi-Tomasi corner detection
            "feature_params": {
                "maxCorners": 50,
                "qualityLevel": 0.1,
                "minDistance": 10,
                "blockSize": 50
            },
            # Parameters for Lucas-Kanade optical flow
            "lk_params": {
                "winSize": [50, 50],
                "maxLevel": 3,
                "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)}
        },
        {
            "name": "5",
            # Parameters for Shi-Tomasi corner detection
            "feature_params": {
                "maxCorners": 50,
                "qualityLevel": 0.2,
                "minDistance": 10,
                "blockSize": 50
            },
            # Parameters for Lucas-Kanade optical flow
            "lk_params": {
                "winSize": [50, 50],
                "maxLevel": 3,
                "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)}
        },
        {
            "name": "6",
            # Parameters for Shi-Tomasi corner detection
            "feature_params": {
                "maxCorners": 50,
                "qualityLevel": 0.3,
                "minDistance": 10,
                "blockSize": 50
            },
            # Parameters for Lucas-Kanade optical flow
            "lk_params": {
                "winSize": [50, 50],
                "maxLevel": 3,
                "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)}
        },
        {
            "name": "7",
            # Parameters for Shi-Tomasi corner detection
            "feature_params": {
                "maxCorners": 50,
                "qualityLevel": 0.1,
                "minDistance": 10,
                "blockSize": 50
            },
            # Parameters for Lucas-Kanade optical flow
            "lk_params": {
                "winSize": [50, 50],
                "maxLevel": 5,
                "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)}
        },
        {
            "name": "8",
            # Parameters for Shi-Tomasi corner detection
            "feature_params": {
                "maxCorners": 50,
                "qualityLevel": 0.1,
                "minDistance": 10,
                "blockSize": 50
            },
            # Parameters for Lucas-Kanade optical flow
            "lk_params": {
                "winSize": [50, 50],
                "maxLevel": 6,
                "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)}
        },
        {
            "name": "9",
            # Parameters for Shi-Tomasi corner detection
            "feature_params": {
                "maxCorners": 50,
                "qualityLevel": 0.1,
                "minDistance": 20,
                "blockSize": 50
            },
            # Parameters for Lucas-Kanade optical flow
            "lk_params": {
                "winSize": [50, 50],
                "maxLevel": 3,
                "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)}
        },

    ]

    for parameter in parameter_list:
        gpu_v2("/home/kubus/Videos/1631281579.mp4", parameter)
