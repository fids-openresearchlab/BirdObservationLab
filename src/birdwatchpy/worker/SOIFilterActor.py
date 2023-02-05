import logging
import time
import traceback
from collections import deque
from heapq import heappush, heappop, nlargest
import ray
from birdwatchpy.logger import get_logger

from birdwatchpy.config import get_soi_thresh_high, get_soi_thresh_low
from birdwatchpy.worker.SequenceExportActor import SequenceExportActor



# Minimum amount of frames for sequences of interest
from birdwatchpy.worker.sparse_opt_flow_worker import SarseOptFlowResult

MIN_FRAMES_IN_SEQUENCE: int = 10

# Define the maximum delta between filtered frames.
MAX_SOI_FRAMES_DELTA: int = 40

# Buffer Size
BUFFER_SIZE: int = 1300


# Define how long to keep frames in buffer before processing (in frame steps). The purpose is to allow to collect
# from threads asynchronously arriving frames.
BUFFER_DELAY: int = 300

# Define how many frames to include before and after the detected sequence
SEQUENCE_PADDING: int = 15

@ray.remote
class SOIFilterActor(object):
    def __init__(self):
        self.logger = get_logger(log_name="FlowThreshSOIFilter", stream_logging_level=logging.DEBUG, file_handler=True,
                            filename="FlowThreshSOIFilter.log")
        self.thresh_low = get_soi_thresh_low()
        self.thresh_high = get_soi_thresh_high()

        self.completed_export_actors = []
        self.current_export_actor = None
        self.current_tasks_on_export_actor = []

        self.first_filtered_frame: int = None
        self.last_filtered_frame: int = None
        self.first_frame_from_buffer: int = None
        self.last_frame_from_buffer: int = None
        self.oldest_frame_number_in_past_soi: int = 0
        self.frame_deque_buffer: deque = deque([])
        self.sparse_opt_res_heap_buffer = []

        self.logger.info("Initialized SOI Detector")

    def add_sparse_opt_flow_res(self, sparse_opt_flow_res):
        """
        Add frame to heapq buffer of the filter.
        """
        # Push new frame to frame heap buffer
        heappush(self.sparse_opt_res_heap_buffer, sparse_opt_flow_res)


    def add_to_frame_buffer(self, args):
        try:
            frame_num, frame_w_img_ref = args
            self.frame_deque_buffer.append((frame_num, frame_w_img_ref))
            self.proc_due_frames() # ToDo: Better place somewhere?
        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")

    def get_frames_from_buffer(self, start, stop):
        try:
            frames=[]
            while True:
                oldest_frame_number, oldest_frame_w_img_ref = self.frame_deque_buffer.popleft()

                if oldest_frame_number < start:
                    continue # Dont do anything with the frame
                elif start <= oldest_frame_number <= stop:
                    frames.append((oldest_frame_number,oldest_frame_w_img_ref))
                elif oldest_frame_number > stop:  # Put back to heap buffer otherwise and break loop
                    self.frame_deque_buffer.appendleft((oldest_frame_number, oldest_frame_w_img_ref))
                    break
                else:
                    self.logger.error(f"Error: Case not matched: start {start}; stop {stop}; oldest_frame_number: {oldest_frame_number} ")
            return frames
        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")

    def clean_frame_buffer_until(self, until_frame_num):
        until_frame_num = until_frame_num - SEQUENCE_PADDING*2
        try:
            start = time.time()
            while True:
                oldest_frame_number, oldest_frame_w_img_ref = self.frame_deque_buffer.popleft()

                if oldest_frame_number < until_frame_num:
                    pass
                else:  # Put back to heap buffer otherwise and break loop
                    self.frame_deque_buffer.appendleft((oldest_frame_number, oldest_frame_w_img_ref))
                    break
        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")

    def get_oldest_frame_num_in_buffer(self):
        oldest_frame_number, oldest_frame_w_img_ref = self.frame_deque_buffer.popleft()
        self.frame_deque_buffer.appendleft((oldest_frame_number, oldest_frame_w_img_ref))
        return oldest_frame_number

    def get_newest_frame_num_in_buffer(self):
        frame_number, frame_w_img_ref = self.frame_deque_buffer.pop()
        self.frame_deque_buffer.append((frame_number, frame_w_img_ref))
        return frame_number

    def proc_due_frames(self):
        try:
            if len(self.sparse_opt_res_heap_buffer) == 0:
                return
            newest_heap_frame, _ = nlargest(1, self.sparse_opt_res_heap_buffer)[0]


            if len(self.sparse_opt_res_heap_buffer) > 0:
                oldest_heap_frame, oldest_movement = heappop(self.sparse_opt_res_heap_buffer)

                latest_frame_num_in_buffer = self.get_newest_frame_num_in_buffer()
                oldest_frame_num_in_buffer = self.get_oldest_frame_num_in_buffer()

                try:
                    assert(oldest_frame_num_in_buffer < oldest_heap_frame)
                except AssertionError:
                    self.logger.error(f"Error: Oldest heap frame is older than oldest frame in buffer. Traceback: {traceback.print_exc()}")

                self.logger.debug(f"""FlowThreshSOIFilter: proc due stats.
                latest_frame_num_in_buffer: {latest_frame_num_in_buffer}
                oldest_frame_num_in_buffer: {oldest_frame_num_in_buffer}
                oldest_frame_number_in_heap: {oldest_heap_frame}
                newest_frame_number_in_heap: {newest_heap_frame}
    
                """)

                # Check if oldest_frame in heap buffer is older than the oldest frame number in past soi. This makes sure that
                # late arriving frames are not processed
                if oldest_heap_frame < self.oldest_frame_number_in_past_soi:
                    self.logger.info(f"FlowThreshSOIFilter: Ignoring late arriving frame.")
                    return

                if oldest_heap_frame < oldest_frame_num_in_buffer:
                    #heappush(self.sparse_opt_res_heap_buffer, (oldest_frame_number, oldest_movement))
                    self.logger.warning(f"""FlowThreshSOIFilter: Frame not in buffer. Either it has not yet arrived or it \
                    is already deleted.
                    latest_frame_num_in_buffer: {latest_frame_num_in_buffer}
                    oldest_frame_num_in_buffer: {oldest_frame_num_in_buffer}
                    oldest_frame_number: {oldest_heap_frame}
                    newest_heap_frame: {newest_heap_frame}
                    
                    """)
                    return


                # Compare frame numbers of oldest frame in heap buffer and newest frame in heap buffer. If the difference is
                # larger than min_age_delta the frame will be process in the filter.
                if oldest_heap_frame < newest_heap_frame - BUFFER_DELAY:
                    self.proc_frame(oldest_heap_frame, oldest_movement)
                else:  # Put back to heap buffer otherwise and break loop
                    heappush(self.sparse_opt_res_heap_buffer, (oldest_heap_frame, oldest_movement))

        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")

    def proc_remaining_frames(self):
        """
        Process remaining frames queued ignoring the age of the filter. This method is on
        """
        while len(self.sparse_opt_res_heap_buffer):
            oldest_heap_frame, oldest_movement = heappop(self.sparse_opt_res_heap_buffer)
            self.proc_frame( oldest_heap_frame, oldest_movement)
        self.logger.info("FlowThreshSOIFilter: All remaining frames processed. Exiting.")

    def init_export_actor(self, frame_num):
        try:
            self.logger.info("FlowThreshSOIFilter: Init ExportActor")
            self.current_export_actor = SequenceExportActor.remote()

            frames_from_buffer = self.get_frames_from_buffer(self.first_filtered_frame - SEQUENCE_PADDING, frame_num)
            assert (len(frames_from_buffer) != 0)
            self.send_frames_to_export_actor(frames_from_buffer)

            self.first_frame_from_buffer = frames_from_buffer[0][0]
            self.last_frame_from_buffer = frames_from_buffer[-1][0]

            self.last_filtered_frame = int(frame_num)
        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")

    def update_export_actor(self, frame_num):
        try:
            assert self.last_frame_from_buffer is not None

            frames_from_buffer = self.get_frames_from_buffer(self.last_frame_from_buffer, frame_num)
            self.send_frames_to_export_actor(frames_from_buffer)
            self.last_frame_from_buffer = int(frames_from_buffer[-1][0])
        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")


    def check_soi_delta_reached(self, frame_num):
        """
        Check if frame number delta to last frame of interest is exceeded.
        """
        return (frame_num - self.last_filtered_frame) > MAX_SOI_FRAMES_DELTA

    def check_first_filtered_exists(self):
        return self.first_filtered_frame is not None

    def check_min_soi_frames_reached(self, frame_num):
        """
        Check if the minimum of Frames in a sequence is reached.
        """
        try:
            return frame_num - self.first_filtered_frame > MIN_FRAMES_IN_SEQUENCE
        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")


    def proc_frame(self, current_frame_number, movement):
        try:
            if self.current_export_actor is None:
                if movement == SarseOptFlowResult.NO_MOVEMENT:
                    if self.check_first_filtered_exists():
                        self.reset()
                    self.clean_frame_buffer_until(current_frame_number)
                    return

                elif movement == SarseOptFlowResult.MOVEMENT:
                    if not self.check_first_filtered_exists():
                        self.first_filtered_frame = current_frame_number
                        self.logger.info("FlowThreshSOIFilter: First Frame Set.")
                    else:
                        if self.check_min_soi_frames_reached(current_frame_number):
                            self.init_export_actor(current_frame_number)
                        else:
                            return

            elif self.current_export_actor is not None:
                if movement == SarseOptFlowResult.MOVEMENT:
                    self.update_export_actor(current_frame_number)
                elif movement == SarseOptFlowResult.NO_MOVEMENT:
                    if self.check_soi_delta_reached(current_frame_number):
                        self.last_filtered_frame=current_frame_number
                        self.update_export_actor(current_frame_number + SEQUENCE_PADDING)
                        self.create_filtered_soi()
                    else:
                        self.update_export_actor(current_frame_number)


        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")

    def send_frames_to_export_actor(self, frames_from_buffer):
        for frame_number, frame_w_img_ref in frames_from_buffer:
            self.current_tasks_on_export_actor.append(self.current_export_actor.add_frame.remote(frame_w_img_ref))


    def create_filtered_soi(self):
        """
        Creates sequence of interest based on the current data in the filter
        """
        try:
            self.logger.info("FlowThreshSOIFilter: Create Filtered SOI")
            # Return if there has not been an actor started
            if self.current_export_actor is None:
                return

            if self.first_frame_from_buffer is None:
                return

            self.oldest_frame_number_in_past_soi = self.last_frame_from_buffer

            ray.wait(self.current_tasks_on_export_actor)
            self.current_export_actor.close_and_rename.remote((self.first_frame_from_buffer, self.last_frame_from_buffer))
            self.completed_export_actors.append(self.current_export_actor)

            # Set oldest_frame_number_in_past_soi to oldest frame in soi in order to ignore late arrival of frames which
            # are already part of processed sequences
            self.oldest_frame_number_in_past_soi = self.last_frame_from_buffer
            self.reset()

        except Exception as e:
            self.logger.error(f"Error: {e} Traceback: {traceback.print_exc()}")


    def reset(self):
        """
        Reset the filter.
        """
        self.current_export_actor = None
        self.current_tasks_on_export_actor = []

        self.first_filtered_frame: int = None
        self.last_filtered_frame: int = None
        self.first_frame_from_buffer: int = None
        self.last_frame_from_buffer: int = None

        self.logger.debug(f"FlowThreshSOIFilter: Resetting.")

    def conclude(self):
        """
        Process remaining data
        """
        self.proc_remaining_frames()
        # Create sequence of interest from data in filter
        self.create_filtered_soi()

        ray.actor.exit_actor()