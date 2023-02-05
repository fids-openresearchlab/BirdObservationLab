import json
import logging
import time
import traceback
from argparse import ArgumentParser
from pathlib import Path
import ray

from birdwatchpy.database import get_relevant_flight_ids_from_sequence
from birdwatchpy.database.sequences_db import insert_sequence, get_sequence_by_id

from birdwatchpy.environment.EnvironmentData import EnvironmentData

from birdwatchpy.logger import get_logger
from birdwatchpy.sequences.SequenceData import SequenceData
from birdwatchpy.sequences.sequences_helper import save_sequence_as_pickle, load_sequence_from_pickle
from birdwatchpy.database import insert_sentence_entry
from birdwatchpy.text_generation.context_aware_productions_manipulation import process_single_flight
from birdwatchpy.text_generation.grammar import create_normalized_PCFG_str, generate_pcfg_sentences, sentence_beautification
from birdwatchpy.text_generation.productions import create_productions_dict
from birdwatchpy.text_generation.grammar import pcfg_from_str
from birdwatchpy.text_generation.productions import load_sentence_prods_from_csv, load_terminal_prods_from_csv
from birdwatchpy.text_generation.productions import as_one_to_one_productions_list
from birdwatchpy.utils import get_project_root


@ray.remote
def detection_and_tracking_task(args):
    logger = get_logger(log_name="detection_and_tracking_task", stream_logging_level=logging.DEBUG, file_handler=True,
                        filename='base.log')
    sequence_dir_path, sequence = args
    logger.info(f"detection_and_tracking_task: started")

    try:
        assert(isinstance(sequence, SequenceData))
        assert(len(sequence.frames)> 0)
    except AssertionError as e:
        logger.exception(
            f"detection_and_tracking_task: Unknown Error.  Exception: {e} Traceback: {traceback.print_exc()}")
        logger.info(f"detection_and_tracking_task: Sequence: {sequence}")
        logger.info(f"detection_and_tracking_task: Frame count: {len(sequence.frames)}")

    try:
        #yolov4_detect(sequence_dir_path, save_out_img=True)
        #time.sleep(2) # ToDo: Remove
        #logger.info(f"detection_and_tracking_task: Successfully ran detections on folder")
        #sequence = extend_sequence_with_darknet_detection(sequence_dir_path, sequence)
        #logger.info(f"detection_and_tracking_task: detection extended sequence:  {sequence}")
        #logger.info(f"Sequence Data:  {sequence}")
        #sequence = tracking_on_sequence(sequence)

        #save_sequence_as_pickle(sequence_dir_path, sequence)
        #logger.info(f"sequence.sequence_id:  {sequence.sequence_id}")
        #logger.info(f"sequence.sequence_id:  {sequence.sequence_id}")
        #logger.info(f"sequence.sequence_id:  {sequence.sequence_id}")

        if len(list(get_sequence_by_id(sequence.sequence_id))) == 0:
            insert_sequence(sequence)
        #insert_sequence(sequence)

        # Text Generation #ToDo: Move somewhere else
        environment_data = EnvironmentData.from_db(list(sequence.frames.values())[0].timestamp)
        logger.info(f"Environment Data:  {environment_data}")

        time.sleep(2) # ToDo: Remove. Only here to make sure data is written to db
        logger.info(f"Flight IDs:  {get_relevant_flight_ids_from_sequence(sequence.sequence_id)}")
        relevant_bird_ids = {flight_id["flight_id"] for flight_id in get_relevant_flight_ids_from_sequence(sequence.sequence_id)}
        logger.info(f"Flight IDs:  {relevant_bird_ids}")
        relevant_birds = [bird for bird in sequence.birds if bird.flight_id in relevant_bird_ids]

        if len(relevant_birds)==0:
            return

        for bird in relevant_birds:
            logger.info("This seems to be a bird?")
            sentence_prods = load_sentence_prods_from_csv(
                get_project_root() / 'birdwatchpy' / 'text_generation' / 'sentence_prod.csv')
            terminal_prods = load_terminal_prods_from_csv(
                get_project_root() / 'birdwatchpy' / 'text_generation' / 'terminal_prod.csv')
            logger.info("Productions loaded")
            processed_productions = process_single_flight("", environment=environment_data, flight=bird,
                                                          sentence_productions_list=sentence_prods,
                                                          terminal_productions_list=terminal_prods)
            logger.info("Productions processed")
            prods_dict = create_productions_dict(as_one_to_one_productions_list(processed_productions))
            logger.info("Productions reated")
            pcfg_str = create_normalized_PCFG_str(prods_dict)
            pcfg = pcfg_from_str(pcfg_str)

            c = 0
            sentence=""
            while True:
                try:
                    logger.info("Try getting a sentence")
                    sentence = generate_pcfg_sentences(pcfg, 1)[0]
                    print(sentence)
                    try:
                        sentence = sentence_beautification(sentence)
                        sentence = sentence.replace("{time}", environment_data.datetime.strftime("%H:%M"))
                        sentence = sentence.replace("{flaps_sec}", str(round(bird.wing_flap_frequency,2)))
                    except Exception as e:
                        logger.error(f"Error in text substraction:  {e} Traceback: {traceback.print_exc()}")
                    break
                except KeyError:
                    logger.info('retry')
                    c+=1
                    if c >= 60000000:
                        logger.error("Error: No Sentence found!")
                        break

                    continue

            if sentence != '':
                insert_sentence_entry({"timestamp": time.time(), "sentence": sentence})

            save_sequence_as_pickle(sequence_dir_path, sequence)
            # Data to be written
            text_dict = {
                f"single_bird_{bird.flight_id}": sentence,
            }

            print(sequence_dir_path / f"single_bird_{bird.flight_id}.json")
            with open(sequence_dir_path / f"single_bird_{bird.flight_id}.json", "w", encoding='utf-8') as outfile:
                json.dump(bird.as_dict(), outfile, ensure_ascii=False)

        with open(sequence_dir_path / "text.json", "w", encoding='utf-8') as outfile:
            json.dump(text_dict, outfile, ensure_ascii=False)

        with open(sequence_dir_path / "environment_data.json", "w", encoding='utf-8') as outfile:
            json.dump(environment_data.as_dict(), outfile, ensure_ascii=False)



            ## Create Bird Flight Folder
            #new_flight_img_folder = sequence_dir_path / bird.flight_id
            #new_flight_img_folder.mkdir(parents=True, exist_ok=True)
            #for frame_num in bird.frame_numbers:
            #    img_name = f"{sequence.sequence_id}-{frame_num}.png"
            #    shutil.copy(sequence_dir_path / "images" / img_name, new_flight_img_folder / img_name)

    except Exception as e:
        logger.error(f"detection_and_tracking_task: Unknown Error.  Exception: {e} Traceback: {traceback.print_exc()}")

    logger.info(f"detection_and_tracking_task: Exiting.")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load from subfolders")
    parser.add_argument("path", help="Input Path")

    args = parser.parse_args()
    detection_and_tracking_tasks = []

    if args.recursive:
        for path in Path(args.path).iterdir():
            if path.is_dir():
                sequence_file_path = Path(f"{path}/{path.name}.sequence")
                if not sequence_file_path.is_file():
                    print("Sequence file not found!")  # ToDo: Logging
                    continue

                print(path)

                sequence = load_sequence_from_pickle(sequence_file_path)
                #detection_and_tracking_tasks.append(detection_and_tracking_task.remote(ray.put((path, sequence))))

                #if len(detection_and_tracking_tasks) > 13:
                #    finished, detection_and_tracking_tasks = ray.wait(detection_and_tracking_tasks)
                ray.wait([detection_and_tracking_task.remote(ray.put((path, sequence)))])

                # write_plain_video(path, sequence)
        ray.wait(detection_and_tracking_tasks)

