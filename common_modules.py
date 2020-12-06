import requests
import json
import shutil
import os
import zipfile
import csv

import config

def check_game_status(gameID):
    api_call_str = config.API_URL+"/game/loadinfo?gameid="+str(gameID)
    gameInfo = requests.get(api_call_str)
    if not gameInfo:
        return -1
    else:
        jdata = json.loads(gameInfo.content)
        if 'success' in jdata and jdata['success'] != True:
            return (-1,jdata)
        else: # game actually found
            return (jdata['game']['status'],jdata)

def download_whole_game(gameID,fName):
    api_call_str = config.API_URL+"/game/loadall?gameid="+str(gameID)

    print("Downloading to "+fName)
    with requests.get(api_call_str, stream=True) as rawstream:
        with open(fName, 'wb') as fp:
            shutil.copyfileobj(rawstream.raw, fp)

def get_game_part_name(gameID):
    return os.path.join(config.GAME_ARCH_DIR, "partial_"+str(gameID)+".zip")

def get_game_full_name(gameID):
    return os.path.join(config.GAME_ARCH_DIR, "full_"+str(gameID)+".zip")

def getPlayerList(gameData):
    playerList = []
    for player in gameData['players']:
        playerList.append(config.RACE_NAME[player['raceid']-1]+" ("+player['username']+")")

    return playerList

def getTempFilesPath():
    return os.path.join(config.GAME_ARCH_DIR,"tmp")

# Cleans the temporary directory from unzipped game files, so we don't fill the hard drive
def cleanTmpDir():
    for file1 in os.listdir(getTempFilesPath()):
        os.remove(os.path.join(getTempFilesPath(), file1))

def unzipGame(fName):
    tmpDir = getTempFilesPath()
    if not os.path.exists(tmpDir):
        os.mkdir(tmpDir)
    else:
        cleanTmpDir()

    with zipfile.ZipFile(fName, 'r') as zip_p:
        zip_p.extractall(getTempFilesPath())

def readMessages(dirName):
    flist = os.listdir(dirName)
    msg_byturn = dict()
    for fname in flist:
        with open(dirName+"/"+fname,'r') as fp:
            try:
                data = json.loads(fp.read()) 
                pid = data['player']['id']
                player_names = []
                for player in data['players']:
                    player_names.append(player['username'])
                if(len(data['mymessages']) > 0):
                    for msg in data['mymessages']:
                        msg_id = msg['id']
                        msg_turn = msg['turn']
                        if not msg_turn in msg_byturn:
                            msg_byturn[msg_turn] = [(player_names,msg_id,msg)]
                        else:
                            msg_byturn[msg_turn].insert(0,(player_names,msg_id,msg))

            except (Exception) as json_err:
                print("Failed to parse "+fname)
    
    return msg_byturn

def getRaceIDs(gameData):
    raceIDs = []
    for player in gameData[1]['players']:
        raceIDs.append(player['raceid'])

    return raceIDs
    

def write_msg_to_csv(msg_byturn,outFile,raceIDs):
    turn_list = sorted(list(msg_byturn.keys()))

    with open(outFile, mode='w') as pOutFile:
        csv_writer = csv.writer(pOutFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        row_header = ['Turn', 'From:', 'To:', 'Body']
        csv_writer.writerow(row_header)
        for msg_turn in turn_list:
            if len(msg_byturn[msg_turn]) > 0: 
                msg_srt_by_id = sorted(msg_byturn[msg_turn], key=lambda tup: tup[1])

                old_from_name = ''
                old_to_name = set()
                old_msg_body = ''
                for msg_tuple in msg_srt_by_id:
                    player_names = msg_tuple[0]
                    msg_id = msg_tuple[1]
                    msg = msg_tuple[2]

                    if msg['messagetype'] == 0:
                        from_id = msg['ownerid']
                        to_id = msg['target']
                    else:
                        to_id = msg['ownerid']
                        from_id = msg['target']

                    from_name = config.RACE_NAME[raceIDs[from_id-1]-1] + " (" + player_names[from_id-1] + ")"
                    to_name = config.RACE_NAME[raceIDs[to_id-1]-1] + " (" + player_names[to_id-1] + ")"

                    if from_name == old_from_name and msg['body'] == old_msg_body:
                        old_to_name.add(to_name)
                    else:
                        if len(old_to_name) > 0:
                            row_list = [msg_turn, old_from_name,
                                ', '.join(str(e) for e in old_to_name),
                                old_msg_body.replace("<br/>","\r\n")]
                            csv_writer.writerow(row_list)
                        old_from_name = from_name
                        old_msg_body = msg['body']
                        old_to_name = set()

                if len(old_to_name) > 0:
                    row_list = [msg_turn, old_from_name,
                        ', '.join(str(e) for e in old_to_name),
                        old_msg_body.replace("<br/>","\r\n")]
                csv_writer.writerow(row_list)
