import logging
import time
import traceback
import ray
from ray.util.queue import Queue

from birdwatchpy.logger import get_logger
from birdwatchpy.optical_flow.sparse.lucas_kanade import LucasKanadeCPU

class Enum:
    pass


class SarseOptFlowResult(Enum):
    MOVEMENT = 1
    NO_MOVEMENT = 2

@ray.remote
def sparse_lk_cpu_worker(args):
    logger = get_logger(log_name="sparse_lk_cpu_worker", stream_logging_level=logging.DEBUG, file_handler=True,
                        filename='base.log')
    logger.info("sparse_lk_cpu_worker: Task Started ")
    queue, soi_filter_actor, params = args
    assert(isinstance(queue, Queue))
    try:

        lk = LucasKanadeCPU(params)

        while True:
            obj_refs = queue.get(block=True, timeout=200)

            frame1, frame1_img =  ray.get(obj_refs[0])
            frame2, frame2_img =  ray.get(obj_refs[1])

            frame1.img_rgb = frame1_img
            frame2.img_rgb = frame2_img

            resulting_frame = lk.calc(frame1, frame2)

            if resulting_frame is not None:
                logger.info(f"sparse_lk_cpu_worker: Sparse Optical Flow processed: {frame1.frame_number} Relevant")
                soi_filter_actor.add_sparse_opt_flow_res.remote(ray.put((frame2.frame_number, SarseOptFlowResult.MOVEMENT)))

            else:
                soi_filter_actor.add_sparse_opt_flow_res.remote(
                    ray.put((frame2.frame_number, SarseOptFlowResult.NO_MOVEMENT))
                )

            #logger.info("sparse_lk_cpu_worker: Sparse Optical Flow processed")

    except Exception as e:
        logger.error(
            f"sparse_lk_cpu_task: Unhandled exception in thread. Exception: {e} Traceback: {traceback.print_exc()}")


@ray.remote
def sparse_lk_cpu_test_task(args):
    logger = get_logger(log_name="sparse_lk_cpu_worker", stream_logging_level=logging.DEBUG, file_handler=True,
                        filename='base.log')
    params, prev_img_ref, img_ref = args

    try:
        #logger.info("sparse_lk_cpu_worker: Task Started ")
        lk = LucasKanadeCPU(params)

        frame1, frame1_img =  ray.get(prev_img_ref)
        frame2, frame2_img =  ray.get(img_ref)

        frame1.img_rgb = frame1_img
        frame2.img_rgb = frame2_img

        start = time.time()
        resulting_frame = lk.calc(frame1, frame2)
        processing_time=time.time()-start

        return (resulting_frame, processing_time)




    except Exception as e:
        logger.error(
            f"sparse_lk_cpu_task: Unhandled exception in thread. Exception: {e} Traceback: {traceback.print_exc()}")