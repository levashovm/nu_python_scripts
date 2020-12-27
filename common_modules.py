import requests
import json
import shutil
import os
import zipfile
import csv
import mailbox
import email
import datetime
import re

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
        
def getPlayerSlotFromName(gameData,userName):
    for playerID in range(len(gameData[1]['players'])):
        if gameData[1]['players'][playerID]['username'] == userName:
            return playerID
    return None

def zipGame(fName):
    tmpDir = getTempFilesPath()
    if os.path.exists(fName):
        os.remove(fName)

    with zipfile.ZipFile(fName,'w',zipfile.ZIP_DEFLATED) as zip_f:
        for f in os.listdir(tmpDir):
            zip_f.write(os.path.join(tmpDir,f),f)
        
    cleanTmpDir()

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

def getRaceIDsLoggedIn(apiKey, gameID):
    raceIDs = []
    payload = {'apikey': apiKey, 'gameid': gameID}
    r = requests.post('https://api.planets.nu/game/loadinfo?version=1', data=payload)
    if r.status_code == 200:
        for player in r.json()['players']:
            raceIDs.append(player['raceid'])
    return raceIDs

def login(username, password):
    payload = {'username': username, 'password': password}
    r = requests.post('http://api.planets.nu/login', data=payload)
    if r.status_code == 200:
        resp = r.json()
        if 'apikey' in resp:
            print('Login successful.')
            return(resp['apikey'])

    print('Login failed.')
    return False


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
                                '\r '.join(str(e) for e in old_to_name),
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


def write_msg_to_mbox(outFile, raceIDs, apiKey, gameID):
    mb = mailbox.mbox(outFile, create=True)
    message_ids = []

    # If the mbox file already exists, find all the message IDs and
    # add them to the list so that we don't push duplicates to the mbox.
    for msg in mb.itervalues():
        message_ids.append(msg['Message-ID'])

    payload = {
        'apikey': apiKey,
        'gameid': gameID,
    }

    # Fetch messages for each player
    for race in raceIDs:
        payload['playerid'] = str(race)
        resp = requests.post('https://api.planets.nu/account/ingameactivity', data=payload)

        if 'activity' in resp.json():
            for msg in resp.json()['activity']:
                # Create a unique ID for not adding duplicates
                msg_id = f"<{str(msg['id'])}.{str(msg['orderid'])}.{str(msg['parentid'])}@{gameID}.planets.nu>"

                # Create a participants list with both sender and recipients
                participants = [emailAddressFromName(i.strip(), gameID) for i in msg['targetname'].split(',')]
                participants.append(emailAddressFromName(msg['sourcename'], gameID))

                if msg_id not in message_ids:
                    # Remove sender from the recipients list. Don't care if something fails.
                    to = participants.copy()
                    try:
                        to.remove(emailAddressFromName(msg['sourcename'], gameID))
                    except ValueError:
                        pass

                    # Construct the message and save to mailbox
                    m = email.message.EmailMessage()
                    m['From'] = emailAddressFromName(msg['sourcename'], gameID)
                    m['To'] = ', '.join(list(set(to)))
                    m['Subject'] = f"Turn {msg['turn']}"
                    m['Message-ID'] = msg_id
                    m['Date'] = datetime.datetime.strptime(msg['dateadded'], '%Y-%m-%dT%H:%M:%S')
                    m.set_content(str(msg['message'].replace("<br/>","\r\n")))
                    mb.add(m)
                    message_ids.append(msg_id)

                for reply in msg['_replies']:
                    # Create a unique ID for not adding duplicates
                    reply_id = f"<{str(reply['id'])}.{str(reply['orderid'])}.{str(reply['parentid'])}@{gameID}.planets.nu>"

                    if reply_id not in message_ids:
                        # Remove sender from the recipients list. Don't care if something fails.
                        to = participants.copy()
                        try:
                            to.remove(emailAddressFromName(reply['sourcename'], gameID))
                        except ValueError:
                            pass

                        # Construct the reply and save to mailbox
                        r = email.message.EmailMessage()
                        r['From'] = emailAddressFromName(reply['sourcename'], gameID)
                        r['To'] = ', '.join(list(set(to)))
                        r['Subject'] = f"Turn {reply['turn']}"
                        r['Message-ID'] = reply_id
                        r['Date'] = datetime.datetime.strptime(reply['dateadded'], '%Y-%m-%dT%H:%M:%S')
                        r['References'] = msg_id
                        r['In-Reply-To'] = msg_id
                        r.set_content(str(reply['message'].replace("<br/>","\r\n")))
                        mb.add(r)
                        message_ids.append(reply_id)

    # Close the mailbox to flush writes
    mb.close()

def emailAddressFromName(name: str, gameID: str):
    email = re.sub(r'\([^()]*\)', '', name)
    return f'"{name}" <{email.replace(" ", "")}@{gameID}.planets.nu>'
