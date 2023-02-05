# Load Data into Scalable

Before you can create your dataset in scalable format you first will need to 
1. Export desired sequences 
2. Convert the exported dataset into MOT Challange format

With the dataset available in MOT format you can now create the scalabel formatted json:

cd scalabel
python3 -m scalabel.label.from_mot --input /media/data/many_bird_export2/MOT --output /media/data/many_bird_export2/scalabel_format_master

