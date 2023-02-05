python_interpreter="/home/kubus/.local/share/virtualenvs/fids_migratory_birds_detection-qEj-P10n/bin/python"

cd ../docker-files
gnome-terminal -- bash -c "sudo docker-compose --env-file ./.env.kubus  up --build mongo nats mongo-express database_service"
cd ..
#export "$(xargs < ./docker-files/.env)"
set -o allexport; source ./docker-files/.env.kubus; set +o allexport

gnome-terminal -- bash -c "$(echo $python_interpreter) ./birdwatchpy/tools/run_sequence_detection_annotation.py; exec bash"


