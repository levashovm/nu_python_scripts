import sys

from common_modules import *
import download_gamedata

def main(argv):
    if(len(sys.argv) < 4):
        usage_msg()
    else:
        (gameData, fName, gameID) = download_gamedata.main(sys.argv[1])

    print("Unzipping archive to " + getTempFilesPath())
    unzipGame(fName)

    raceIDs = getRaceIDs(gameData)

    print("Extracting messages")
    msg_byturn = readMessages(getTempFilesPath())

    outFile = "messages_" + str(gameID) + ".csv"
    write_msg_to_csv(msg_byturn, outFile, raceIDs)
    print("Messages saved to "+outFile)

    cleanTmpDir()

    apiKey = login(sys.argv[2], sys.argv[3])
    outFile = "messages_" + str(gameID) + ".mbox"
    write_msg_to_mbox(outFile, raceIDs, apiKey, gameID)
    print("Messages saved to "+outFile)


def usage_msg():
    print("Usage: python pull_messages.py GAME_ID USERNAME PASSWORD")
    print("Only completed games are currently supported")
    quit()


if __name__ == "__main__":
    main(sys.argv)
