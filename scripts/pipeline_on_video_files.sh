cd ..
for file in /mnt/fids_data/streamed_footage/pipeline/*.avi
do
  python3 ./StreamReceiver.py --src $file --type video --feature_detector goodftt --work_dir /media/fids/work_ssd/nextcloud_new_grammar/ 
done
