from dataclasses import dataclass

from bbox_utils.bbox_2d import BoundingBox
from bson import ObjectId


@dataclass
class DetectionData:
    # detection_run_id: int
    class_id: int
    confidence: float
    bb: BoundingBox

    def as_dict(self)  -> dict:
        detection_data_dict = self.__dict__
        detection_data_dict["bb"] = [xy.tolist() for xy in detection_data_dict["bb"].to_xyxy()]

        return detection_data_dict



def DetectionDataFactory(detection_dict):
    print(detection_dict)
    detection_dict["bb"] = BoundingBox.from_xyxy(detection_dict["bb"][0], detection_dict["bb"][1])
    return DetectionData(**detection_dict)



def default(obj):
    print(f"IsInstance? : ", {isinstance(obj, BoundingBox)})
    print(type(obj))
    if isinstance(obj, BoundingBox):
        return obj.to_xyxy()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError