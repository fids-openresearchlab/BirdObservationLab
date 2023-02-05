import configparser
import csv
import glob
from _csv import reader
from glob import glob
from pathlib import Path
from typing import List, Sequence

import numpy as np
from PIL import Image
from bbox_utils import BoundingBox

from birdwatchpy.detection.DetectionData import DetectionData
from birdwatchpy.frames.FrameData import FrameData


def load_mot_det(txt_file_path, session_id="detection") -> Sequence[FrameData]:
    data = []

    with open(txt_file_path, 'r') as read_obj:
        csv_reader = reader(read_obj, delimiter=",")
        list_of_rows = list(csv_reader)

        last_frame_num = int(max(list_of_rows, key=lambda item: int(item[0]))[0])

        for frame_num in range(last_frame_num):
            converted_det = []
            for det in np.array(list(filter(lambda item: int(item[0]) == frame_num, list_of_rows))).astype(
                    np.float):
                assert (det[0] == frame_num)
                bbox = BoundingBox.from_xywh((det[2], det[3]), det[4], det[5]).to_xyxy()

                converted_det.append(DetectionData(class_id=0, confidence=det[6], bb=bbox))  # ToDo: Class is hardcoded
                data.append(FrameData())


def load_yolov4_annotations(path, session_id) -> Sequence[FrameData]:
    data = []
    for txt_file_path in list(glob.glob(f'{path}/*.txt')):
        with open(txt_file_path, 'r') as read_obj:
            frame_num = int(str(Path(txt_file_path).stem).split("-")[1])
            frame_data = FrameData(session_id, frame_num, has_birds=True, is_ambiguous=False)
            csv_reader = reader(read_obj, delimiter=" ")
            list_of_rows = list(csv_reader)

            for row in list_of_rows:
                frame_data.gt_bboxes.append(DetectionData(row[0],
                                                          confidence=1,
                                                          bb=BoundingBox.from_yolo((float(row[1]), float(row[2])),
                                                                                   float(row[3]), float(row[4]),
                                                                                   (2160, 3840))
                                                          ))
                data.append(frame_data)
    return data


def create_mot_folder_structure(name: str, path: Path):
    """
    The create_mot_folder_structure function creates a folder structure for the MOT dataset.
    The function takes in a path to where you want the folder structure to be created and creates
    a &quot;MOT&quot; directory with two subdirectories, &quot;img&quot;, and &quot;det&quot;.

    """
    mot_path = Path(path) / f"MOT-{name}"
    mot_path.mkdir(parents=True, exist_ok=True)
    mot_img_path = mot_path / "img1"
    mot_img_path.mkdir(parents=True, exist_ok=True)
    det_path = Path(f"{mot_path}/det/det.txt")
    gt_path = Path(f"{mot_path}/gt/gt.txt")
    det_path.parents[0].mkdir(parents=True, exist_ok=True)
    gt_path.parents[0].mkdir(parents=True, exist_ok=True)

    return mot_path, mot_img_path, det_path, gt_path


def save_mot_det(sequence_name: str, data: List[FrameData], path: Path, out_path):
    """
    The save_mot function saves the data in a MOT format.
    It takes as input:
    - data: List[FrameData] - The list of frames to be saved. Each frame is represented by FrameData object, which contains all the information about that frame (see FrameData class).
    - out_path: str - The path where to save the MOT folder. It will be created if it does not exist yet.

    """
    mot_path, mot_img_path, det_path, gt_path = create_mot_folder_structure(sequence_name, out_path)

    seqLength = len(data)
    config = configparser.ConfigParser()
    seqinfo_ini = Path(f"{mot_path}/seqinfo.ini")  # Path of your .ini file
    config["Sequence"] = {
        'name': f'MOT-{sequence_name}',
        'imDir': 'img1',
        'frameRate': '29.97',
        'seqLength': f'{seqLength}',
        'imWidth': '3840',
        'imHeight': '2160',
    }
    config.write(seqinfo_ini.open("w"), space_around_delimiters=False)

    with open(det_path, 'w') as det, open(gt_path, 'w') as gt:
        # create the csv writer
        det_writer = csv.writer(det)
        gt_writer = csv.writer(gt)

        sorted_frame_data = sorted(data, key=lambda it: it.frame_number)
        assert len(data) == sorted_frame_data[-1].frame_number + 1 - sorted_frame_data[0].frame_number, f"""The number of
        frames in the supplied frame data ({len(data)}) should be the same as the the last frame number substracted by
        the first frame number ({sorted_frame_data[-1].frame_number - sorted_frame_data[0].frame_number})."""

        track_id = 0
        for frame_num, frame_data in enumerate(sorted_frame_data, 1):
            if not Path(mot_img_path / f"{frame_num:06}.jpg").exists():
                img_png = Image.open(path / "images" / f'{sequence_name}-{frame_data.frame_number}.png')
                img_png.save(mot_img_path / f"{frame_num:06}.jpg", quality=100, subsampling=0)

            # for gt_bb in frame_data.gt_bboxes:
            #     bb_xywh = gt_bb.bb.to_xywh()
            #
            #     if False:
            #         img = cv.imread(str(Path(out_path / f'{sequence_name}-{frame_data.frame_number}.png')))
            #         cv.rectangle(img, gt_bb.bb.to_xyxy()[0], gt_bb.bb.to_xyxy()[1], (0, 255, 0), 3)
            #         cv.rectangle(img, gt_bb.bb.to_xyxy()[0], gt_bb.bb.to_xyxy()[1], (0, 255, 0), 3)
            #         img = cv.resize(img, (1920, 1080), interpolation=cv.INTER_AREA)
            #         cv.imshow("image", img)
            #         cv.waitKey(3000)
            #
            #     gt_writer.writerow([frame_num, -1,  # gt_bb.class_id,
            #                         bb_xywh[0][0],
            #                         bb_xywh[0][1],
            #                         bb_xywh[1],
            #                         bb_xywh[2],
            #                         1, 1, #gt_bb.class_id,
            #                         -1])

            for det in frame_data.detection:
                # write a row to the csv file
                bb_xywh = det.bb.to_xywh()
                track_id += 1

                # img = cv.imread(str(Path(out_path / f'{sequence_name}-{frame_data.frame_number}.png')))
                # cv.rectangle(img, det.bb.to_xyxy()[0], det.bb.to_xyxy()[1], (0, 255, 0), 3)
                # cv.rectangle(img, det.bb.to_xyxy()[0], det.bb.to_xyxy()[1], (0, 255, 0), 3)
                # cv.imshow("image", img)
                # cv.waitKy(3000)

                det_writer.writerow([frame_num, -1,  # gt_bb['class_id'],
                                     bb_xywh[0][0],
                                     bb_xywh[0][1],
                                     bb_xywh[1],
                                     bb_xywh[2],
                                     det.confidence,
                                     det.class_id, -1])

                # Following lines only write detection as mot ground truth data
                gt_writer.writerow([frame_num, track_id,  # gt_bb.class_id,
                                    bb_xywh[0][0],
                                    bb_xywh[0][1],
                                    bb_xywh[1],
                                    bb_xywh[2],
                                    1, 1,  # gt_bb.class_id,
                                    -1])
