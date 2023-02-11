# Setup configuration
BirdObservationLab is configured using the config.ini file. 

```ini
[general]
local_data_path = /path/to/local_data
fps = 29.97
resolution_width =3840
resolution_height=2160

; Defines how long images are saved in the temporary folder
tmp_storage_duration=750

[database]
mongo_db_host =
mongo_db_port =
mongo_db_user = 
mongo_db_pw =

[detection]
; Defines path to yolov3 weights file
path_to_weights=

; Defines path to yolov3 cfg file
path_to_cfg=

; Defines path to yolov3 names file
path_to_names=

[sequence-of-interest-filter]
thresh_low=4
thresh_high=3000
```