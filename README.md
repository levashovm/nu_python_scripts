# nu_python_scripts
Python scripts for interacting with planets.nu

Requires python to be installed on the computer: https://www.python.org/downloads/

1. pull_messages.py script

Use:
python pull_messages.py [GAME_ID]

GAME_ID is the 6-digit numeric game number that can be found in game history or in the URL of the game.

The script will:

a) check that the game exists and has finished (only finished games supported at the moment)

b) create a game_data/tmp local folder and download the game_data into the folder as a zip file

c) unzip the file into a game_data/tmp

d) extract all of the messages and export them into messages_[GAME_ID].csv file.  The csv file can be opened using any text editor or Excel/Excel-like program

e) remove the files from game_data/tmp to save disk space

f) the zip file will remain in game_data folder.  It can be deleted
