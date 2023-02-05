from pathlib import Path
from typing import Tuple

from birdwatchpy.exceptions import PathnameFormatException, SequenceIDFormatException


def extract_info_from_filestem(sequence_id_str: str) -> dict:
    """

    Args:
        path:

    Returns: Tuple consisting of sequence_id, session_id, first_frame_number, last_frame_number

    """
    info = sequence_id_str.split("_")
    if len(info) == 3:
        return {"sequence_id": sequence_id_str, "session_id": int(info[0]), "from_frame_number": int(info[1]),
                "to_frame_number": int(info[2])}
    if len(info) == 4:
        return {"sequence_id": sequence_id_str, "session_id": f"{info[0]}_{info[1]}", "from_frame_number": int(info[2]),
                "to_frame_number": int(info[3])}
    if len(info) == 5:
        return {"sequence_id": sequence_id_str, "session_id": f"{info[0]}_{info[1]}_{info[2]}", "from_frame_number": int(info[3]),
                "to_frame_number": int(info[4])}
    else:
        raise SequenceIDFormatException(
            "Pathname not in the required format {session_id}_{first_frame}_{last_frame}. Pathname: " + sequence_id_str)




def extract_info_from_sequence_pathname(path: Path) -> dict:
    """

    Args:
        path:

    Returns: Tuple consisting of sequence_id, session_id, first_frame_number, last_frame_number

    """
    try:
        info = extract_info_from_filestem(path.stem)
    except SequenceIDFormatException:
        raise PathnameFormatException(
            "Pathname not in the required format {session_id}_{first_frame}_{last_frame}. Pathname: " + path.as_posix())

    return info
