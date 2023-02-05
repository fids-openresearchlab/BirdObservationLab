import shutil
from argparse import ArgumentParser
from pathlib import Path


from birdwatchpy.bird_flight_analysis import BirdFlightData

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load flights")
    parser.add_argument("path", help="Input Path")

    dataset_folder = Path("/media/fids/work_ssd/nextcloud/dataset_18_05/from_dataset_folder")
    dataset_folder.mkdir(parents=True, exist_ok=True)

    args = parser.parse_args()
    if args.recursive:
        for path in Path(args.path).iterdir():
            if path.is_dir():
                print(path)
                for flight_file in Path(path).glob('single_bird*.json'):
                    print(flight_file)
                    bird = BirdFlightData.load(flight_file.as_posix())

                    bird_folder =dataset_folder / f"{bird.flight_id}"
                    bird_folder.mkdir(parents=True, exist_ok=True)

                    shutil.copy(flight_file, bird_folder / flight_file.name)
                    shutil.copy(flight_file.parent / "environment_data.json", bird_folder / "environment_data.json")
                    shutil.copy(flight_file.parent / "text.json", bird_folder / "text.json")



                    print(bird)


                    frame_num = bird.frame_numbers[int(len(bird.frame_numbers)/3)]
                    try:
                        glob_list=list((path / "images").glob(f"*{frame_num}.png"))
                        img_name = glob_list[0]
                        shutil.copy(img_name, bird_folder / f"bird.png")
                    except Exception as e:
                        print(e)

