import json
import time
from pathlib import Path
from typing import Sequence, List

from bbox_utils import BoundingBox

from birdwatchpy.detection.DetectionData import DetectionData
from birdwatchpy.frames.FrameData import FrameData


def load_from_darkhelp_format(path, session_id="detection") -> List[FrameData]:
    with open(path) as json_file:
        parsed_data = json.load(json_file)
        frame_data_list: Sequence[FrameData] = []
        for frame in parsed_data['file']:
            if 'annotated_image' in frame:
                frame_num = int(Path(frame['annotated_image']).stem.split("-")[-1])
            else:
                frame_num = int(Path(frame['filename']).stem.split("-")[-1])
            # Warning! This function creates timestamps for frames based on the time of execution and not capture of the frame!
            frame_data = FrameData(session_id, frame_num, time.time())
            frame_data.detection = []
            if not "prediction" in frame:
                continue
            for prediction in frame["prediction"]:
                for probability in prediction["all_probabilities"]:
                    frame_data.detection.append(
                        DetectionData(probability["class"],
                                      probability["probability"],
                                      BoundingBox.from_xywh(
                                          (prediction["rect"]["x"], prediction["rect"]["y"]),
                                          prediction["rect"]["width"],
                                          prediction["rect"]["height"]
                                      )))
            frame_data_list.append(frame_data)
        return frame_data_list
