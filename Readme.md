
# SWG Audit Assistant

Secure Web Gateway Audit Assistant - Python utility that provides help with finding unused configuration items in McAfee/Skyhigh SWG/Proxy.


## Features

- Detects Unused Lists
- Detects Unused Settings
- Detects Disabled Rules
- Exceptions Support


## Usage/Examples
```bash
usage: Assistant.py [-h] [-v] [-e EXCEPTIONS] [-l] [-lx LISTS_EXCEPTIONS] [-s] [-sx SETTINGS_EXCEPTIONS] [-r] [-rx RULES_EXCEPTIONS] [-u USERNAME] backupfile

Detects unused and disabled configuration items in Secure Web Gateway configuration.

positional arguments:
  backupfile            Backup file from SWG or URL address of SWG.

options:
  -h, --help            show this help message and exit
  -v                    Prints a status on the screen
  -e EXCEPTIONS, --exceptions EXCEPTIONS
                        Path to the file with the general exceptions
  -l                    Enables general exceptions on the lists.
  -lx LISTS_EXCEPTIONS, --lists-exceptions LISTS_EXCEPTIONS
                        Enables specific exceptions on the lists.
  -s                    Enables general exceptions on the settings.
  -sx SETTINGS_EXCEPTIONS, --settings-exceptions SETTINGS_EXCEPTIONS
                        Enables specific exceptions on the settings.
  -r                    Enables general exceptions on the rules.
  -rx RULES_EXCEPTIONS, --rules-exceptions RULES_EXCEPTIONS
                        Enables specific exceptions on the rules.
  -u USERNAME, --username USERNAME
                        Username to SWG Rest API.
```

Simple Usage:
```javascript
python Assistant.py mcafee.backup
```
Verbose Usage:
```javascript
python Assistant.py -v mcafee.backup
```
Exceptions Usage:
```javascript
python Assistant.py -lx exceptions.txt mcafee.backup
```
Online Usage:
```javascript
python Assistant.py https://192.168.1.20:4712
```
Common exceptions for settings and lists, specific for rules:
```javascript
python Assistant.py -sle common.txt -rx specific.txt https://192.168.1.20:4712
```
## Authors

- [@firewallops](https://www.firewallops.com)

