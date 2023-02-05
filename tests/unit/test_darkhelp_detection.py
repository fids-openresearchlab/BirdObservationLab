from birdwatchpy.detection import yolov4_detect
from tests.fixtures.fixtures import sequence_fixture_path


def test_yolov4_detect():
    status_code = yolov4_detect(sequence_fixture_path)
    assert status_code == 0, "Could not run darkhelp command. Check if required drivers and CUDA toolkit are installed."