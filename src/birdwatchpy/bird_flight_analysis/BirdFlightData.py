import json
import math
from copy import deepcopy
from typing import List, Sequence, Optional

import numpy as np
from imgaug.augmentables.bbs import BoundingBox
from scipy.fft import fft, fftfreq
from yupi import Trajectory

from birdwatchpy.environment.EnvironmentData import EnvironmentData
from birdwatchpy.utils.polar.conversion import cart2pol, direction_lookup


class BirdFlightData:
    def __init__(self, flight_id: str, sequence_id: str, frame_numbers: List[int], bb_arrays: np.ndarray):
        """
        A BirdFlightData object contains trajectory and other features of an object. It potentially is a flying
        bird.

        Parameters
        ----------
        flight_id : string
            String identifying the flight with a unique id.
        bb_arrays : np.ndarray
            Array containing bounding boy positions.

        Args:
        flight_id(str): Flight ID of the track

        :param bb_arrays: Array of tracking bounding boxes

        Attributes
        ----------

        Examples
        --------
        You can create a BirdFlightData object by giving the arrays representing the bounding boxes of the tracked
        objects:

        #ToDo: Give an example


        Raises
        ------
        (to be completed)
        """
        # ToDo: Bad implementation. Necessary because tracking returns negative bb positions
        bb_arrays = [np.where(bb < 0, 0, bb) for bb in np.array(bb_arrays)]
        # bb_arrays = list(filter(lambda bb: bb.all(0), bb_arrays))

        self.flight_id = flight_id
        self.sequence_id = sequence_id

        # Ground Truth Data
        self.gt_is_bird: Optional[bool] = None

        # Frame Numbers
        self.frame_numbers = frame_numbers

        # Create sequence of BoundingBoxes
        self.bounding_boxes: Sequence[BoundingBox] = [
            BoundingBox(bb_array[0], bb_array[1], bb_array[2], bb_array[3]) for bb_array in bb_arrays]

        # Create positions from BoundingBoxes
        self.positions: List[List[int]] = [(bb.center_x, bb.center_y) for bb in self.bounding_boxes]
        self.positions_count = len(bb_arrays)

        # Create yupi trajectory for further analysis
        self.y_traj = Trajectory(points=self.positions, traj_id=flight_id)

        # Velocities and speed
        self.velocities = self.y_traj.v
        self.mean_vel: float = self.y_traj.features.mean_vel
        self.speed: List[float] = self.y_traj.v.norm
        self.avg_speed: float = np.mean(self.speed).astype(float)

        # Length and displacement
        self.distances: List[float] = self.y_traj.delta_r.norm
        self.displacement: float = self.y_traj.features.displacement
        self.length: float = self.y_traj.features.length

        # Straightness
        self.straightness_dict: dict = {}
        self.prepare_straightness_values()

        # Size and related analysis
        self.sizes: List[float] = [bb.area for bb in self.bounding_boxes]
        self.avg_size: float = np.average(self.sizes)

        self.wing_flap_frequency, _, _ = self.calc_wing_flap_freq()

        # Other
        self.max_speed_deviation = max(self.speed) - min(self.speed)
        self.flight_direction: Optional[str] = None

    def get_flight_direction_char(self):
        if not self.flight_direction:
            return None
        else:
            return direction_lookup(self.flight_direction)

    def set_flight_direction(self, environment_data: EnvironmentData):
        if self.straightness_dict["1/1"] > 0.8:  # ToDo: Value hardcoded. Adjust?
            flight_vector = self.y_traj.r[-1] - self.y_traj.r[0]
            flight_angle, _ = cart2pol(flight_vector[0], flight_vector[1])
            self.flight_direction = flight_angle - environment_data.get_north_angle()
        else:
            self.flight_direction = None
            flight_angle = None

        return flight_angle, self.flight_direction

    def prepare_straightness_values(self, depth=8):
        # ToDo: Don't round but find other solution. Middle point?
        for d in range(1, depth):
            pos = [math.floor(self.positions_count / d * i - 1) for i in range(1, d + 1)]
            pos.insert(0, 0)
            for i in range(1, d + 1):
                self.straightness_dict.update({f"{i}/{d}": self.calculate_straightness_between(pos[i - 1], pos[i])})

    def calculate_straightness_between(self, start_idx: int, end_idx: int):
        """
        Calculated straightness between two points by dividing the displacement between endpoints with the distance
        traveled along the trajectory (like the crow flies).
        Args:
            start_idx (int): index of the start position
            end_idx (int): index of the end position
        Returns:
            float: Straightness

        """
        traj = deepcopy(self.y_traj)
        displacement = (traj.r[end_idx] - traj.r[start_idx]).norm
        length = sum(traj.delta_r[start_idx:end_idx].norm)

        return 0 if (displacement == 0 or length == 0) else displacement / length

    def calc_wing_flap_freq(self):
        """
        Calculate the wing flap frequency.

        Returns:
            float: Wing Flap Frequency
        """
        # ToDo: Clean up! Better Implementation!
        # Number of samples
        N = self.positions_count

        if N < 8:  # ToDo: Short flight should be filtered out somewhere else!
            return None, None, None

        yf = fft(np.array(self.sizes) / 1000)
        xf = fftfreq(N) * 30

        a = np.abs(yf)[2:]
        n = len(a)
        k = 4
        ms = -10 ** 6
        ws = sum(a[:k])
        res = []
        for i in range(n - k):
            if ws > ms:
                pos = i
                res.append(xf[2:][pos])
            ms = max(ms, ws)
            ws = ws - a[i] + a[i + k]
        ms = max(ms, ws)

        return abs(res[-1]), xf, yf

    def as_dict(self) -> dict:
        flight_data_dict = deepcopy(self)
        flight_data_dict.bounding_boxes = [(bb.x1, bb.y1, bb.x2, bb.y2,) for bb in self.bounding_boxes]
        flight_data_dict.velocities = self.velocities.__array__().tolist()
        flight_data_dict.speed = self.speed.__array__().tolist()
        flight_data_dict.avg_speed = self.avg_speed.__array__().tolist()
        flight_data_dict.distances = self.distances.__array__().tolist()
        del flight_data_dict.y_traj  # Delete yupi trajectory as it can not be serialized

        return flight_data_dict.__dict__

    @classmethod
    def load(cls, path: str):
        with open(path) as f:
            data = f.read()
        js = json.loads(data)
        return cls.load_from_dict(js)

    @staticmethod
    def from_bb():
        pass

    @classmethod
    def load_from_dict(cls, flight_dict: dict):
        return cls(flight_dict["flight_id"], flight_dict["sequence_id"], flight_dict["frame_numbers"],
                   bb_arrays=flight_dict["bounding_boxes"])
