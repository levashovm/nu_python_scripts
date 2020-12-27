import requests
import sys
import json
import shutil
import os

import config
from common_modules import *

def main(argv):
    if(len(argv) < 1):
        usage_msg()
    else:
        try:
            gameID = int(argv[0])
        except (ValueError) as verr:
            usage_msg()

    gameData = check_game_status(gameID)
    gameStatus = gameData[0]

    if(len(gameData) > 1):
        print(gameData[1]['game']['name'])

    if not os.path.exists(config.GAME_ARCH_DIR):
        os.mkdir(config.GAME_ARCH_DIR)
    fName_part = get_game_part_name(gameID)
    fName_full = get_game_full_name(gameID)

    if(gameStatus == config.GAME_STATUS_ERROR):
        print("Game "+str(gameID)+" not found")
    elif(gameStatus == config.GAME_STATUS_INTEREST or gameStatus == config.GAME_STATUS_NEW):
        print("Game "+str(gameID)+" not started")
    elif(gameStatus == config.GAME_STATUS_IN_PROGRESS):
        print("Game "+str(gameID)+" in progress")
        #print("Loading for games in progress not yet supported")

        if(len(argv) < 3):
            usage_msg()
            
        apiKey = login(argv[1],argv[2])
        if apiKey:
            if os.path.exists(fName_part):
                print("Found partial game file.  Downloading missing turns.")
                unzipGame(fName_part)
            currTurn = gameData[1]['game']['turn']
            playerID = getPlayerSlotFromName(gameData,argv[1]) 
            if not playerID:
                print("Could not find username"+argv[1]+" in the game")
            else:
                for k in range(currTurn):
                    fName_out = os.path.join(getTempFilesPath(),'player'+str(playerID+1)+'-turn'+str(k+1)+'.trn')
                    if not os.path.exists(fName_out):
                        print('Downloaling turn '+str(k+1))
                        payload = {'gameid': gameID, 'playerid': playerID+1,'apikey': apiKey, 'turn': k}
                        r = requests.post('http://api.planets.nu/game/loadturn', data=payload)                
                        f = open(fName_out,"w")
                        rst_data = json.loads(r.text)
                        f.write(json.dumps(rst_data['rst']))
                        f.close()
                        
                zipGame(fName_part)       
            return (gameData,fName_part,gameID)
        else:
            disp('Login failed')
            quit()
    elif(gameStatus == 3):
        print("Game "+str(gameID)+" is finished")
        if not os.path.exists(fName_full):
            if os.path.exists(fName_part): # Assume that game completed between script runs
                print("Found partial game file.  Re-downloading as full")
                os.path.remove(fName_part)
            download_whole_game(gameID,fName_full)
        else:
            print("Whole game file "+fName_full+" is already present")
        return (gameData,fName_full,gameID)

def usage_msg():
    #print("Usage: python download_gamedata.py GAME_#")
    #print("       Only completed games are supported at the moment")
    print("Usage: python download_gamedata.py GAME_# [USERNAME] [PASSWORD]")
    print("    USERNAME and PASSWORD are required for games still in progress")
    quit()

if __name__ == "__main__":
    main(sys.argv[1:])
