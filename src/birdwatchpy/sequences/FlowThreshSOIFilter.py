import copy
import logging
from heapq import heappush, heappop, nlargest
from typing import List

from birdwatchpy.optical_flow.sparse.SparseOpticalFlowResultsData import FrameData
from birdwatchpy.sequences.SequenceData import SequenceData
from birdwatchpy.logger import get_logger
from birdwatchpy.utils import get_project_root

logger = get_logger(log_name="FlowThreshSOIFilter", stream_logging_level=logging.DEBUG, file_handler=True,
                    log_file_path=(get_project_root() / "logs" / "base.log").as_posix())

# Minimum amount of frames for sequences of interest
MIN_FRAMES_IN_SEQUENCE: int = 20

# Define the maximum delta between filtered frames.
MAX_SOI_FRAMES_DELTA: int = 120

# Define how long to keep frames in buffer before processing (in frame steps). The purpose is to allow to collect
# from threads asynchronously arriving frames.
BUFFER_DELAY: int = 200

# Define how many frames to include before and after the detected sequence
SEQUENCE_PADDING: int = 30


class FlowThreshSOIFilter:
    def __init__(self, thresh_low: float, thresh_high: float):
        self.thresh_low = thresh_low
        self.thresh_high = thresh_high
        self.results: List[FrameData] = []
        self.last_filtered_frame: FrameData = None
        self.oldest_frame_number_in_past_soi: int = 0
        self.resulting_soi: List[SequenceData] = []

        self.frame_heap_buffer = []

        print("Initialized SOI Detector")

    def next(self, new_frame_data: FrameData):
        """
        Add frame to heapq buffer of the filter.
        """
        logger.debug(f"FlowThreshSOIFilter: Received new processed frame.")

        # Push new frame to frame heap buffer
        heappush(self.frame_heap_buffer, new_frame_data)

    def proc_due_frames(self):
        if len(self.frame_heap_buffer) == 0:
            return
        newest_frame = nlargest(1, self.frame_heap_buffer)[0]
        while len(self.frame_heap_buffer) > 0:
            oldest_frame = heappop(self.frame_heap_buffer)

            # Check if oldest_frame in heap buffer is older than the oldest frame number in past soi. This makes sure that
            # late arriving frames are not processed
            if oldest_frame.frame_number < self.oldest_frame_number_in_past_soi:
                logger.debug(f"FlowThreshSOIFilter: Ignoring late arriving frame.")
                return

            # Compare frame numbers of oldest frame in heap buffer and newest frame in heap buffer. If the difference is
            # larger than min_age_delta the frame will be process in the filter.
            if oldest_frame.frame_number < newest_frame.frame_number - BUFFER_DELAY:
                self.proc_frame(oldest_frame)
            else:  # Put back to heap buffer otherwise and break loop
                heappush(self.frame_heap_buffer, oldest_frame)
                break

    def proc_remaining_frames(self):
        """
        Process remaining frames queued ignoring the age of the filter. This method is on
        """
        while len(self.frame_heap_buffer):
            oldest_frame = heappop(self.frame_heap_buffer)
            self.proc_frame(oldest_frame)
        logger.info("FlowThreshSOIFilter: All remaining frames processed. Exiting.")

    def proc_frame(self, frame_data: FrameData):
        distances = [flow.distance for flow in frame_data.sparse_opt_flow]
        for distance in distances:
            if self.thresh_low < float(distance) < self.thresh_high:
                self.last_filtered_frame = frame_data
                self.results.append(frame_data)
                logger.debug(
                    f"FlowThreshSOIFilter: Frame of interest detected. Max distance: {max(distances)}. Frame Number: {frame_data.frame_number}")
                break
            else:
                logger.debug(
                    f"FlowThreshSOIFilter: Frame not relevant. max distance: {max(distances)}. Frame Number: {frame_data.frame_number}")

        if not self.last_filtered_frame:
            return

        # Check if frame number delta to last frame of interest is exceeded. If so, process sequence.
        if frame_data.frame_number - self.last_filtered_frame.frame_number > MAX_SOI_FRAMES_DELTA:
            frames_in_soi = max(self.results, key=lambda frame: frame.frame_number).frame_number - min(self.results,
                                                                                                       key=lambda
                                                                                                           frame: frame.frame_number).frame_number
            if frames_in_soi < MIN_FRAMES_IN_SEQUENCE:
                logger.info("FlowThreshSOIFilter: Sequence is too small to be a Sequence of interest. Reset filter.")
                self.reset()
            elif frames_in_soi > MIN_FRAMES_IN_SEQUENCE:
                logger.info("FlowThreshSOIFilter: Sequence of Interest Detected")
                self.create_filtered_soi()

    def create_filtered_soi(self):
        """
        Creates sequence of interest based on the current data in the filter
        """

        # Return if filter is empty
        if len(self.results) == 0:
            return

        logger.info(f"FlowThreshSOIFilter: Create sequence of interest.")

        frame_numbers = [result.frame_number for result in self.results]
        # Get from_frame_number and handle negative frame_numbers due to substraction
        from_frame_number = min(frame_numbers) - SEQUENCE_PADDING
        from_frame_number = 0 if from_frame_number < 0 else from_frame_number
        to_frame_number = max(frame_numbers) + SEQUENCE_PADDING

        frames = {frame_number: None for frame_number in range(from_frame_number, to_frame_number + 1, 1)}
        # Fill frame dictionary with processed frames. Note: Missing frames are added from buffer in the
        # StreamReceiver.
        for frame in self.results:
            frames[frame.frame_number] = frame

        self.resulting_soi.append(
            SequenceData(self.results[0].session_id, from_frame_number=from_frame_number,
                         to_frame_number=to_frame_number, frames=frames))

        # Set oldest_frame_number_in_past_soi to oldest frame in soi in order to ignore late arrival of frames which
        # are already part of processed sequences
        self.oldest_frame_number_in_past_soi = min(frame_numbers)
        self.reset()

    def get_filtered_soi(self) -> List[SequenceData]:
        """
        Get all filtered sequences of interest and remove them from the filter
        """
        filtered_soi = copy.deepcopy(self.resulting_soi)
        self.resulting_soi = []
        return filtered_soi

    def reset(self):
        """
        Reset the filter.
        """
        self.results = []
        self.last_filtered_frame = None
        logger.debug(f"FlowThreshSOIFilter: Resetting.")

    def conclude(self):
        """
        Process remaining data
        """
        self.proc_remaining_frames()
        # Create sequence of interest from data in filter
        self.create_filtered_soi()
