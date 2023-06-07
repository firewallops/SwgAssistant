import argparse
from library.SWGassistant.SwgAssistant import SwgAuditAssistant

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detects unused and disabled configuration items in Secure Web Gateway configuration.')
    parser.add_argument('backupfile', default="xml.backup", type=str, help='Backup file from SWG or URL address of SWG.')
    parser.add_argument('-v', help="Prints a status on the screen", action='store_true')
    parser.add_argument('-e', "--exceptions", type=str, help="Path to the file with the general exceptions")
    parser.add_argument('-l', help="Enables general exceptions on the lists.", action='store_true')
    parser.add_argument('-lx', '--lists-exceptions', help="Enables specific exceptions on the lists.")
    parser.add_argument('-s', help="Enables general exceptions on the settings.", action='store_true')
    parser.add_argument('-sx', '--settings-exceptions', help="Enables specific exceptions on the settings.")
    parser.add_argument('-r', help="Enables general exceptions on the rules.", action='store_true')
    parser.add_argument('-rx', '--rules-exceptions', help="Enables specific exceptions on the rules.")
    parser.add_argument('-u', '--username', type=str, help="Username for SWG Rest API.")
    args = parser.parse_args()

    print(f"[*] [Info] Analyzing configuration backup: {args.backupfile}") if args.v else None
    swg = SwgAuditAssistant(args)
    swg.start()
    print(f"[*] [Info] Generating Reports.") if args.v else None
    swg.doReport()
    print(f"[*] [Info] Done!") if args.v else None
    

