import logging
import os
import subprocess
import traceback
from pathlib import Path

from birdwatchpy.config import get_yolov4_weights_path, get_yolov4_cfg_path, get_yolov4_names_path
from birdwatchpy.logger import get_logger

logger = get_logger(log_name="detection", stream_logging_level=logging.DEBUG, file_handler=True,
                    filename='base.log')


# The Tiles Edge value controls how close to the edge of a tile an object must be to be considered for re-combining when
# both tiling and recombining have been enabled. The smaller the value, the closer the object must be to the edge of a
# tile. The factor is multiplied by the width and height of the detected object. Possible range to consider would be
# 0.01 to 0.5. If set to zero, then the detected object must be right on the tile boundary to be considered.
# More Info: https://www.ccoderun.ca/darkhelp/api/classDarkHelp_1_1Config.html#add15d57a384c7eb827078b4b3a279b79
TILES_EDGE_FACTOR = 0.4

# This value controls how close the rectangles needs to line up on two tiles before the predictions are combined.

# This is only used when both tiling and recombining have been enabled. As the value approaches 1.0, the closer the
# rectangles have to be "perfect" to be combined. Values below 1.0 are impossible, and predictions will never be
# combined. Possible range to consider might be 1.10 to 1.50 or even higher; this also depends on the nature/shape of
# the objects detected and how the tiles are split up. For example, if the objects are pear-shaped, where the smaller
# end is on one tile and the larger end on another tile, you may need to increase this value as the object on the
# different tiles will be of different sizes. The default is 1.20.
# More Info: https://www.ccoderun.ca/darkhelp/api/classDarkHelp_1_1Config.html#add15d57a384c7eb827078b4b3a279b79
TILES_RECT_FACTOR = 2.7

def yolov4_detect(sequence_dir_path: Path, save_out_img=True, engine="darknet"):
    try:
        (sequence_dir_path / "yolov4_out").mkdir(parents=False, exist_ok=True)
        image_dir_path = sequence_dir_path / 'images'
        img_list_string = ""
        img_list = []
        for img_name in map(lambda path: path.name, sorted(list(image_dir_path.glob("*.png")))):
            img_list.append(str(img_name))

        path_to_weights = get_yolov4_weights_path()
        path_to_cfg = get_yolov4_cfg_path()
        path_to_names = get_yolov4_names_path()

        command = f"""Darknet command: {' '.join(['DarkHelp', '--json', '--autohide', 'off', '--tiles', 'on', '--tile-edge', '0.4',
                                                  '--tile-rect', '2.7', '--duration', 'off', '--nms', '0.2', '--threshold', '0.05', path_to_weights,
                                                  path_to_cfg, path_to_names, '--outdir', (sequence_dir_path / 'yolov4_out').as_posix(), '--keep'] + img_list)}"""


        command_list = ['DarkHelp', '--json', '--autohide', 'off', '--tiles', 'on', '--tile-edge', '0.4',
                  '--tile-rect', '2.7', '--duration', 'off', '--nms', '0.2', '--threshold', '0.05', path_to_weights,
                   path_to_cfg, path_to_names, '--outdir', (sequence_dir_path / 'yolov4_out').as_posix(), '--keep'] + img_list


        try:
            status_code = subprocess.call(command_list, shell=False,  env={'PATH': os.getenv('PATH')}, cwd=str(image_dir_path))
            # output = subprocess.call(['DarkHelp', '--json', '--driver', 'opencv', '--autohide', 'off', '--tiles', 'on', '--tile-edge', '0.4',
            #       '--tile-rect', '2.7', '--duration', 'off', '--nms', '0.2', '--threshold', '0.05', path_to_weights,
            #       path_to_cfg, path_to_names, '--outdir', (sequence_dir_path / 'yolov4_out').as_posix(), '--keep'] + img_list, stderr=subprocess.STDOUT)
        except Exception as e:
            logger.error(e.returncode)

        if int(status_code) != 0:
            logger.error(f"Could not run Darknet command: '{command}'")

        return status_code

        # stderr = p.communicate()
    except Exception as e:
        logger.exception(f"detection: Unhandled exception in thread.{e} {traceback.print_exc()}")



if __name__ == "__main__":
    yolov4_detect(Path("/media/fids/work_ssd/tmp/sequences/isar_biber1645051762merged_0000307_0000577/images"))
