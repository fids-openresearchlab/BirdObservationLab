#ToDo: get rid of link to interpreter
#python_interpreter="/home/kubus/.local/share/virtualenvs/fids_migratory_birds_detection-qEj-P10n/bin/python"
python_interpreter="/home/jo/.var/app/com.jetbrains.PyCharm-Professional/data/virtualenvs/fids_bird_detection_and_tracking-jrQ4Gl_l/bin/python"

cd ../docker-files
gnome-terminal -- bash -c "sudo docker-compose --env-file ../.env  up --build mongo nats mongo-express database_service"
cd ..
#export "$(xargs < ./docker-files/.env)"
set -o allexport; source ./docker-files/.env.kubus; set +o allexport

gnome-terminal -- bash -c "$(echo $python_interpreter) ./birdwatchpy/worker/database_service.py; exec bash"
sleep 2s
gnome-terminal -- bash -c "$(echo $python_interpreter) ./birdwatchpy/worker/cuda_sparse_optical_flow_processing.py -label "lk sparse with fast detector jan 7" -source /mnt/kubus/kubus_data/data/ressources/footage; exec bash"
