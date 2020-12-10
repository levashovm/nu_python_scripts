import sys
import argparse

from common_modules import *
import download_gamedata

def main():
    parser = argparse.ArgumentParser(
        description='Pull messages in CSV or mbox format.',
        epilog='NOTE: Only completed games are currently supported!'
    )
    parser.add_argument('--format', choices=['csv', 'mbox'], default='csv', help='Select either csv or mbox (default csv)')
    parser.add_argument('--username', '-u', help='planets.nu username (required when using mbox format)')
    parser.add_argument('--password', '-p', help='planets.nu password (required frem using mbox format)')
    parser.add_argument('GAMEID', help='Game ID to download messages from (must be finished)')
    args = parser.parse_args()

    if args.format == 'mbox' and (args.username is None or args.password is None):
        parser.error("--format mbox requires --username and --password.")

    if args.format == 'csv':
        (gameData, fName, gameID) = download_gamedata.main(args.gameid)

        print("Unzipping archive to " + getTempFilesPath())
        unzipGame(fName)

        raceIDs = getRaceIDs(gameData)

        print("Extracting messages")
        msg_byturn = readMessages(getTempFilesPath())

        outFile = "messages_" + str(gameID) + ".csv"
        write_msg_to_csv(msg_byturn, outFile, raceIDs)
        print("Messages saved to "+outFile)

        cleanTmpDir()

    else:
        apiKey = login(args.username, args.password)
        if apiKey:
            raceIDs = getRaceIDsLoggedIn(apiKey, args.gameid)
            outFile = f'messages_{args.gameid}.mbox'
            write_msg_to_mbox(outFile, raceIDs, apiKey, args.gameid)
            print(f'Messages saved to {outFile}')


if __name__ == "__main__":
    main()
