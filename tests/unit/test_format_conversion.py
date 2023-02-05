from birdwatchpy.label import create_mot_folder_structure, save_mot_det


def test_load_mot_det():
    assert False


def test_load_darkhelp():
    assert False


def test_save_mot(tmp_path):
    save_mot_det(tmp_path)
    assert ((tmp_path / 'seqinfo.ini').exists())


def test_create_mot_folder_structure(tmp_path):
    name = 'test'
    create_mot_folder_structure(name, tmp_path)

    assert ((tmp_path / f'MOT-{name}').exists())
    assert ((tmp_path / 'MOT' / 'det').exists())
    assert ((tmp_path / 'MOT' / 'gt').exists())
