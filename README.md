# nu_python_scripts
Python scripts for interacting with planets.nu

Requires python to be installed on the computer: https://www.python.org/downloads/

## pull_messages.py script

```bash
usage: pull_messages.py [-h] [--format {csv,mbox}] [--username USERNAME] [--password PASSWORD] GAMEID
```

`GAMEID` is the 6-digit numeric game number that can be found in game history or in the URL of the game.

### Pulling messages in CSV (comma separated values) format

CSV format is the default.  For finished games, you only need to give the `GAMEID` value to the script.  For games still in progress, your planets.nu USERNAME and PASSWORD are also required.

```bash
python pull_messages.py --username USERNAME --password PASSWORD GAMEID
```
When using the CSV format, the script will:

a) check that the game exists.  If the game is still in progress, it will login 

b) create a game_data/tmp local folder and download the game_data into the folder as a zip file

c) unzip the file into game_data/tmp

d) extract all of the messages and export them into `messages_[GAMEID].csv` file.  The csv file can be opened using any text editor or Excel/Excel-like program

e) remove the files from game_data/tmp to save disk space

i) the zip file will remain in game_data folder.  It can be deleted

### Pulling messages in mbox format

When pulling messages for a game in mbox format, it's then possible to import the mbox file into an e-mail reader to read the in-game messages. When using mbox format, you need to give the following parameters to the script:

```bash
python pull_messages.py --format mbox --username USERNAME --password PASSWORD GAMEID
```

The script will:

a) log in to planets.nu with the given username and password

b) fetch all messages for all races in the game

c) extract all the messages in mbox format to `messages_[GAMEID].mbox` file. The file can be imported to an e-mail program such as Thunderbird or Outlook.  (Thunderbird requires a plugin, such as "ImportExportTools NG" to import mbox files).

NOTE: It's possible that not all messages are fetched when using the mbox format. For example, for Capricorn war, only about the most recent 150 turns worth of messages was received when testing this script.
