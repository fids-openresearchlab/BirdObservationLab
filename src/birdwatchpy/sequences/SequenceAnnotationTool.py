from copy import copy
from pathlib import Path
from typing import Dict

import cv2 as cv
from bson import ObjectId

from birdwatchpy.database import sequences_db

from birdwatchpy.frames.frame_extractor import extract_frame_from_video
from birdwatchpy.img_processing.write_frames import write_frame_image
from birdwatchpy.optical_flow.sparse.sparse_viz import simple_lines_draw
from birdwatchpy.sequences.SequenceData import SequenceData

window_size = (1920, 1080)


class SequenceAnnotationTool:
    def __init__(self, sequence: SequenceData):
        self.sequence = sequence
        self.frames: Dict = {}
        if self.check_already_annotated() == True:
            self.is_already_annotated = True
            return
        self.is_already_annotated = False

        for frame_num in self.sequence.frame_numbers:
            self.load_frame_data(frame_num)

        self.show_annotations: bool = True

    def check_already_annotated(self):
        for frame_num in self.sequence.frame_numbers:
            frame_data = get_frame_by_session_and_frame_number(self.sequence.session_id, frame_num)

            # if not "has_birds" in frame_data or frame_data.has_birds == True or :
            if frame_data.get("has_birds") is None and frame_data.get("is_ambiguous") is None:
                print(f"Following frame was not included has not been annotated {frame_num}")
                return False

        return True

    def load_frame_data(self, frame_num):
        self.frames[frame_num] = {}
        self.frames[frame_num]["img"] = extract_frame_from_video(self.sequence.session_id, frame_num)
        self.frames[frame_num]["frame_data"] = get_frame_by_session_and_frame_number(self.sequence.session_id,
                                                                                     frame_num)
        self.frames = {k: v for k, v in sorted(self.frames.items(), key=lambda item: item[0])}

    def run(self):
        if self.check_already_annotated():
            self.is_already_annotated = True
            return

        while True:
            for frame_number, frame in self.frames.items():
                img = frame["img"].copy()
                if self.show_annotations:
                    old_points = tuple(
                        map(lambda e: (e["x_old"], e["y_old"]),
                            frame["frame_data"]["sparse_opt_flow"]["sparse 005 qual"]["flow"]))
                    new_points = tuple(
                        map(lambda e: (e["x_new"], e["y_new"]),
                            frame["frame_data"]["sparse_opt_flow"]["sparse 005 qual"]["flow"]))
                    img = simple_lines_draw(old_points, new_points, img)
                    cv.putText(img, f'Frame Number: {frame["frame_data"]["frame_number"]}', (120, 20),
                               cv.FONT_HERSHEY_SIMPLEX, 1,
                               (255, 255, 255), 2)

                resized_frame = cv.resize(img, window_size,
                                          interpolation=cv.INTER_AREA)
                cv.imshow("Sequence Loop", resized_frame)
                k = cv.waitKey(100)
                if k != -1:
                    print(f"Key Pressed: {k}")
                if k == 49:  # 1 # toggle current image
                    cv.destroyAllWindows()
                    self.frame_by_frame_annotation()
                    return
                elif k == 48:  # 0
                    self.sequence.has_birds = False
                    self.reject_frames()
                    self.update_frames_db()
                    cv.destroyAllWindows()
                    return
                elif k == 99:  # c
                    print("Close sequence annotation")
                    cv.destroyAllWindows()
                    return

    def frame_by_frame_annotation(self):
        current_frame_num = list(self.frames)[0]
        self.sequence.has_birds = False
        while True:
            frame = self.frames[current_frame_num]
            img = copy(frame["img"])
            if self.show_annotations:
                old_points = tuple(map(lambda e: (e["x_old"], e["y_old"]),
                                       frame["frame_data"]["sparse_opt_flow"]["sparse 005 qual"]["flow"]))
                new_points = tuple(map(lambda e: (e["x_new"], e["y_new"]),
                                       frame["frame_data"]["sparse_opt_flow"]["sparse 005 qual"]["flow"]))

                # assert (old_points != new_points)

                img = simple_lines_draw(old_points, new_points, img)

                cv.putText(img, f'Frame:{frame["frame_data"]["session_id"]} #{frame["frame_data"]["frame_number"]}',
                           (5, 20),
                           cv.FONT_HERSHEY_SIMPLEX, 1,
                           (255, 255, 255), 2)

                if "has_birds" in frame["frame_data"]:
                    cv.putText(img, f'has birds: {frame["frame_data"]["has_birds"]}', (10, 50), cv.FONT_HERSHEY_SIMPLEX,
                               1,
                               (255, 255, 255), 2)
                if "is_ambiguous" in frame["frame_data"]:
                    cv.putText(img, f'is_ambiguous: {frame["frame_data"]["is_ambiguous"]}', (15, 50),
                               cv.FONT_HERSHEY_SIMPLEX,
                               1,
                               (255, 255, 255), 2)

            resized_frame = cv.resize(img, window_size,
                                      interpolation=cv.INTER_AREA)
            cv.imshow("Individual Frames", resized_frame)

            k = cv.waitKey(0)
            print(k)
            if k == 49:  # 1 # toggle current image
                print("Bird in frame")
                self.frames[current_frame_num]["frame_data"]["has_birds"] = True
                self.sequence.has_birds = True
                continue
            elif k == 48:  # 0 48
                print("No bird in frame")
                self.frames[current_frame_num]["frame_data"]["has_birds"] = False
                continue
            elif k == 32:  # 0 48
                print("Toggle show annotation")
                self.show_annotations = not self.show_annotations
                continue
            elif k == 53:  # 0 48
                print("Frame is ambiguous")
                self.frames[current_frame_num]["frame_data"]["is_ambiguous"] = True
                self.sequence.is_ambiguous = True
                continue

            elif k == 119:  # W
                print("Write Image")
                cv.imwrite(f"{frame['frame_data']['session_id']}_{frame['frame_data']['frame_number']}.png", img)
                continue
            elif k == 97:  # a
                print("Show previous frame")
                if not current_frame_num - 1 in self.frames.keys():
                    print("add new frame")
                    self.load_frame_data(current_frame_num - 1)
                current_frame_num -= 1
                continue
            elif k == 100:  # d
                print("Show next Frame")
                if current_frame_num + 1 not in self.frames.keys():
                    print("add new frame")
                    self.load_frame_data(current_frame_num + 1)
                current_frame_num += 1
                continue
            elif k == 99:  # c
                print("Close and save current sequence annotation")
                self.process_sequence()
                cv.destroyAllWindows()
                return

        cv.destroyAllWindows()

    def reject_frames(self):
        for frame in self.frames.values():
            frame["frame_data"]["has_birds"] = False

    def update_frames_db(self):
        for frame in self.frames.values():
            if "has_birds" in frame["frame_data"]:
                set_frames_has_birds(ObjectId(frame["frame_data"]["_id"]), frame["frame_data"]["has_birds"])
            if frame["frame_data"]["is_ambiguous"] is not None:
                set_frames_is_ambiguous(ObjectId(frame["frame_data"]["_id"]), self.sequence.is_ambiguous)

    def update_sequence_db(self):
        print("Sequence of Interest Detected")  # ToDo: logging
        frame_numbers = [frame_number for frame_number in self.frames]
        sequence_id = f"{self.sequence.session_id}_{min(frame_numbers):07d}_{max(frame_numbers):07d}"
        sequence = SequenceData(self.sequence.session_id, from_frame_number=min(frame_numbers),
                                to_frame_number=max(frame_numbers),
                                frames={frame.frame_number: frame for frame in self.frames},
                                has_birds=self.sequence.has_birds, is_ambiguous=self.sequence.is_ambiguous)
        sequences_db.upsert_sequence(sequence)

    def export(self, export_video, export_img):
        frame_numbers = [frame_number for frame_number in self.frames]
        sequence_id = f"{self.sequence.session_id}_{min(frame_numbers):07d}_{max(frame_numbers):07d}"

        if export_video:
            path = Path(
                "")

            out = cv.VideoWriter(f"{sequence_id}.mp4", cv.VideoWriter_fourcc(*'mp4v'), 29.95,
                                 (1920, 1080))
            out.release()

        for frame in self.frames.values():
            if export_img:
                if frame["frame_data"]["has_birds"]:
                    write_frame_image(frame["img"], frame["frame_data"], folder=f"./{sequence_id}",
                                      show_detections=False)
            if export_video:
                resized_frame = cv.resize(frame["frame_data"], (1920, 1080),
                                          interpolation=cv.INTER_AREA)
                out.write(resized_frame)

        if export_video:
            out.release()

    def process_sequence(self):
        print("Update frames in db")
        self.update_frames_db()
        print("Upsert sequence to db")
        self.update_sequence_db()
        # print("Exporting files")
        # self.export(True, True)
