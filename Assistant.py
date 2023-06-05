import argparse
from library.SWGassistant.SwgAssistant import SwgAuditAssistant

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detects unused and disabled configuration items in Secure Web Gateway configuration.')
    parser.add_argument('backupfile', default="xml.backup", type=str, help='Backup file from SWG or URL address of SWG.')
    parser.add_argument('-v', help="Prints a status on the screen", action='store_true')
    parser.add_argument('-e', "--exceptions", type=str, help="Path to the file with the exceptions")
    parser.add_argument('-l', help="Enables exceptions on the lists.", action='store_true')
    parser.add_argument('-u', '--username', type=str, help="Username to SWG Rest API.")
    args = parser.parse_args()

    print(f"[*] [Info] Analyzing configuration backup: {args.backupfile}") if args.v else None
    swg = SwgAuditAssistant()
    if args.backupfile.startswith("http"):
        swg.URL = args.backupfile
    else:
        swg.FILE = args.backupfile
    swg.exceptions = args.exceptions
    swg.listExceptions = args.l
    swg.USERNAME = args.username
    swg.start()
    print(f"[*] [Info] Generating Reports.") if args.v else None
    swg.doReport()
    print(f"[*] [Info] Done!") if args.v else None
    

