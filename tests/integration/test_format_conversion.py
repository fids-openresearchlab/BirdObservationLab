import pytest

from birdwatchpy.label import save_mot_det, load_mot_det
from birdwatchpy.sequences import load_sequence_from_pickle
from tests.fixtures.fixtures import sequence_file_fixture_path


@pytest.mark.integtest
def test_mot_save_and_load(tmp_path):
    sequence_fixture_data = load_sequence_from_pickle(path=sequence_file_fixture_path)
    save_mot_det(sequence_fixture_data.sequence_id, sequence_fixture_data.frames.values(), sequence_file_fixture_path,
                 out_path=tmp_path)

    det_file_path = tmp_path / f'MOT-{sequence_fixture_data.sequence_id}' / 'det' / 'det.txt'
    assert det_file_path.exists()

    load_mot_det(det_file_path)
