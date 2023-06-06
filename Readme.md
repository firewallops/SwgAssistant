# SWG Audit Assistant

Secure Web Gateway Audit Assistant - Python utility that provides help with finding unused configuration items in McAfee/Skyhigh SWG/Proxy.


## Features

- Detects Unused Lists
- Detects Unused Settings
- Detects Disabled Rules
- Exceptions Support


## Usage/Examples

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
python Assistant.py -le exceptions.txt mcafee.backup
```
Online Usage:
```javascript
python Assistant.py https://192.168.1.20:4712
```
## Authors

- [@firewallops](https://www.firewallops.com)
