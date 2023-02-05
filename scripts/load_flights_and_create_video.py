from argparse import ArgumentParser
from pathlib import Path
from typing import List
from random import randint
import cv2
from imgaug import BoundingBox

from birdwatchpy.bird_flight_analysis import BirdFlightData
from birdwatchpy.detection.DetectionData import DetectionData
from birdwatchpy.sequences import SequenceData
from birdwatchpy.sequences import extract_info_from_filestem
from birdwatchpy.sequences import load_sequence_from_pickle

color = []
n = 15
for i in range(n):
    color.append((randint(0, 255),randint(0, 255),randint(0, 255)))

def draw_tracking_bb_on_image(frame_num:int, img, bird_flights: List[BirdFlightData]):
    for i,flight in enumerate(bird_flights):
        index_list = [index for index, fn_flight in enumerate(flight.frame_numbers) if frame_num == fn_flight]
        if len(index_list)==0:
            continue
        img = flight.bounding_boxes[index_list[0]].draw_box_on_image(img, color=color[i], size=3)
    return img

def draw_detection_bb_on_image(img, detections: List[DetectionData]):
    [BoundingBox(det.bb.tl[0],det.bb.tl[1],det.bb.br[0],det.bb.br[1]).draw_box_on_image(img, color=(0,0,255), size=5, copy=False) for det in detections if det.confidence > 0.17]
    return img
    #img = flight.bounding_boxes[index_list[0]].draw_box_on_image(img, color=color[i], size=3)

def create_videos_from_folders(path:Path, out_path: Path, draw_track_bb:bool = False, draw_detection_bb:bool=False, resize:bool=True, prefix:str=''):
    for path in path.iterdir():
        if path.is_dir():
            print(path)

            if len(list(Path(path).glob('*.sequence'))) == 0:
                continue

            sequence_info = extract_info_from_filestem(path.stem)
            sequence_filepath = path / f"{sequence_info['sequence_id']}.sequence"
            if sequence_filepath.is_file():
                sequence: SequenceData = load_sequence_from_pickle(sequence_filepath)
            else:
                continue

            if len(list(Path(path).glob('single_bird*.json'))) > 0:
                set_of_image_paths = set([])
                birds = []
                for flight_file in Path(path).glob('single_bird*.json'):
                    bird = BirdFlightData.load(flight_file.as_posix())
                    birds.append(bird)
                    set_of_image_paths = set_of_image_paths.union(set(bird.frame_numbers))

                list_of_img_paths = list(set_of_image_paths)
                list_of_img_paths.sort()

                resolution = (1280, 1024) if resize else ((3840, 2160))

                out_filename = f"{out_path}/{prefix}{path.name}.avi"
                out = cv2.VideoWriter(out_filename, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10,
                                      resolution)

                for frame_num in list_of_img_paths:
                    img_path = path / "images" / f"{path.name}-{frame_num}.png"
                    assert img_path.is_file()
                    print(img_path)
                    img = cv2.imread(img_path.as_posix())

                    if draw_track_bb:
                        img = draw_tracking_bb_on_image(frame_num, img, birds)

                    if draw_detection_bb:
                        img = draw_detection_bb_on_image(img, detections = [det for det in sequence.frames[frame_num].detection])

                    if resize:
                        img =cv2.resize(img, resolution, interpolation=cv2.INTER_LINEAR)
                    out.write(img)

                out.release()
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load flights")
    parser.add_argument("--draw_track_bb", action='store_true', help="Draw Tracking BoundingBoxes")
    parser.add_argument("--draw_detection_bb", action='store_true', help="Draw Detection Bounding Boxes")
    parser.add_argument("--resize", action='store_true', help="Recursively load flights")
    parser.add_argument("--out", help="Output Path")
    parser.add_argument("path", help="Input Path")

    args = parser.parse_args()
    if args.recursive:
        create_videos_from_folders(Path(args.path),Path(args.out), resize=args.resize,  draw_detection_bb = True, prefix= 'det_' )




