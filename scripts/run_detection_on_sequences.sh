#ToDo: get rid of link to interpreter
#python_interpreter="/home/kubus/.local/share/virtualenvs/fids_migratory_birds_detection-qEj-P10n/bin/python"
python_interpreter="/home/jo/.var/app/com.jetbrains.PyCharm-Professional/data/virtualenvs/fids_bird_detection_and_tracking-jrQ4Gl_l/bin/python"

cd ../docker-files
gnome-terminal -- bash -c "sudo docker-compose --env-file ../.env  up --build mongo nats mongo-express database_service detection_yolov4_service soi_processing_service"
cd ..
#export "$(xargs < ./docker-files/.env)"
set -o allexport; source ./.env; set +o allexport
gnome-terminal -- bash -c "$(echo $python_interpreter) ./birdwatchpy/worker/process_soi_worker.py; exec bash"
gnome-terminal -- bash -c "$(echo $python_interpreter) ./birdwatchpy/tools/initiate_sequences_processing.py; exec bash"


