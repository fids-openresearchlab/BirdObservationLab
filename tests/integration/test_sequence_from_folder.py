import pytest

from birdwatchpy.sequences import create_new_sequence_from_path
from birdwatchpy.sequences import load_sequence_from_pickle
from tests.fixtures.fixtures import sequence_fixture_path, sequence_file_fixture_path


@pytest.mark.integtest
def test_sequence_from_path_compared_to_sequence_pickle():
    sequence_from_path = create_new_sequence_from_path(path=sequence_fixture_path, load_detections=True)
    sequence_fixture_data = load_sequence_from_pickle(path=sequence_file_fixture_path)

    assert len(sequence_from_path.frames) == len(sequence_fixture_data.frames)

    sequence_fixture_data.birds = []
    sequence_fixture_data.frames = []
    sequence_from_path.frames = []
    assert sequence_from_path == sequence_fixture_data
