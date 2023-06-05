import argparse
from library.SWGassistant.SwgAssistant import SwgAuditAssistant
print("Dev")
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detects unused and disabled configuration items in Secure Web Gateway configuration.')
    parser.add_argument('backupfile', default="xml.backup", type=str, help='Backup file from SWG.')
    parser.add_argument('-v', help="Prints a status on the screen", action='store_true')
    parser.add_argument('-e', "--exceptions", type=str, help="Path to the file with the exceptions")
    parser.add_argument('-l', help="Enables exceptions on the lists.", action='store_true')
    args = parser.parse_args()

    print(f"[*] [Info] Analyzing configuration backup: {args.backupfile}") if args.v else None
    swg = SwgAuditAssistant()
    swg.FILE = args.backupfile
    swg.exceptions = args.exceptions
    swg.listExceptions = args.l
    swg.start()
    print(f"[*] [Info] Generating Reports.") if args.v else None
    swg.doReport()
    print(f"[*] [Info] Done!") if args.v else None
    

