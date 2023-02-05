from pathlib import Path

import cv2


def get_filenames_by_type_gen(file_type: str, path: Path):
    print(path)
    # print(type(path))
    pathlist = sorted(path.glob(file_type))
    for path in pathlist:
        print(path)
        yield Path(path)


def get_filenames_recursively_by_type(file_type: str, path: Path):
    for path in Path(path).rglob(file_type):
        yield Path(path)


def get_img_data_from_folder_gen(path: Path):
    for files in get_filenames_by_type_gen("*.png", path):
        yield cv2.imread(str(files))
