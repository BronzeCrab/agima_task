#### What is it:

This is python based json-to-html converter daemon.

#### Features:

- logging (by default to /tmp/converter.log)
- works like a daemon, dont block terminal

#### How to install:

`pip install -r requirements.txt`

#### How to start and control:

Next u can do:

`python converter.py -start`  

 to start.

`python converter.py -status`  

to get status (it will be displayed in log). By default log is `/tmp/converter.log`. U can change
log folder just by editing `log_file` variable.

`python converter.py -stop`  

 to stop it.

You can change name of input file by editing `INPUT_FILE_NAME` var.
You can change directory to look in by editing `FOLDER_TO_LOOK_IN` var.
Outputs to the `FOLDER_TO_LOOK_IN` dir.