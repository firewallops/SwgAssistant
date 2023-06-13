# Import Section
import xml.etree.ElementTree as ET
from glob import glob
import argparse
from os import path, mkdir, remove
from library.SWGunpack.SwgUnpack import SwgUnpack
import csv
from shutil import rmtree, move
from datetime import datetime
from urllib.request import build_opener, HTTPSHandler
import ssl
from urllib.parse import urlencode
from getpass import getpass
import urllib

# Class Definition
class SwgAuditAssistant:
    def __init__(self, args) -> None:
        self._baseCfgPath = ""
        self._settingsXmlFileNames = ""
        self._settingsNames = ""
        self._policyXmlLoaded = False
        self.exceptions = args.exceptions
        self.listFlag = args.l
        self.ruleFlag = args.r
        self.settingsFlag = args.s
        self.listExceptions = args.lists_exceptions
        self.ruleExceptions = args.rules_exceptions
        self.settingsExceptions = args.settings_exceptions
        self.URL = ""
        self.FILE = ""
        self.stamp = datetime.strftime(datetime.now(), "%Y_%m_%d-%H_%M")
        self.USERNAME = args.username
        if args.backupfile.startswith("http"):
            self.URL = args.backupfile
        else:
            self.FILE = args.backupfile
    
    def start(self):
        if (self.FILE != "") and (self.FILE.endswith(".backup")):
            self.offline(self.FILE)
            return
        elif (self.URL != "") and (self.URL.startswith("http")):
            self.online()
            return
        print("Please provide a valid backup name or API URL.")
        exit()

    def online(self):
        # Login, download backup and logout
        self._logout(self.downloadBackup(self._login()))
        # Proceed offline
        self.offline(self.FILE)

    def offline(self, configXmlFile):
        self._fileExists(configXmlFile)
        self.FILE = configXmlFile
        self._validateArguments()       
        args = argparse.Namespace(backupfile=configXmlFile, outpath='.', v=False)
        SwgUnpack(args)
        self._get_baseCfgPath()
        if self._baseCfgPath != "":
            self._detectUnusedSettings()
            self._detectDisabledRules()
            self._detectUnusedLists()
            self._cleanup()

    def _validateArguments(self):
        if self.exceptions is not None:
            self._fileExists(self.exceptions)
            if not any([self.listFlag, self.ruleFlag, self.settingsFlag]):
                print("[*] [Warning] Don't know where to apply the general exceptions! Skipping.")
        if self.listExceptions is not None:
            self._fileExists(self.listExceptions)
        if self.settingsExceptions is not None:
            self._fileExists(self.settingsExceptions)
        if self.ruleExceptions is not None:
            self._fileExists(self.ruleExceptions)
        if self.listFlag and self.listExceptions:
            print("[*] [Warning] [Lists] Specific exceptions will override general exceptions!")
        if self.settingsFlag and self.settingsExceptions:
            print("[*] [Warning] [Settings] Specific exceptions will override general exceptions!")
        if self.ruleFlag and self.ruleExceptions:
            print("[*] [Warning] [Rules] Specific exceptions will override general exceptions!")

    def _get_baseCfgPath(self):
        if path.exists("default"):
            self._baseCfgPath = f"{[ x for x in glob('default/*') if path.isdir(x)][0]}/"
    
    def _getFromPolicyFile(self, element="rule"):
        if not self._policyXmlLoaded:
            gwrsPolicyFile = path.join(self._baseCfgPath, "gwrs.xml" )
            self._gwrsXml = ET.parse(gwrsPolicyFile)
            self._policyXmlLoaded = True
        return  self._gwrsXml.findall(f".//{element}")
    
    def _getXmlFromDir(self, dir):
        self._settingsXmlFileNames = glob(f"{self._baseCfgPath}{dir}/*.xml")
        return [s.split("/")[-1].rstrip(".xml") for s in self._settingsXmlFileNames]

    def _detectUnusedSettings(self):
        settingsNames = self._getXmlFromDir("cfg")
        # Extract enableEngineActionContainer
        temp_usedSettings_1 = [action.get("configurationId") for action in self._getFromPolicyFile("enableEngineActionContainer") if action.get("configurationId") != None]
        # Extract executeActionContainer
        temp_usedSettings_2 = [action.get("configurationId") for action in self._getFromPolicyFile("executeActionContainer") if action.get("configurationId") != None]
        # Extract propertyInstance
        temp_usedSettings_3 = [action.get("configurationId") for action in self._getFromPolicyFile("propertyInstance") if action.get("configurationId") != None]
        # Extract actionContainer
        temp_usedSettings_4 = [action.get("configurationId") for action in self._getFromPolicyFile("actionContainer") if action.get("configurationId") != None]
        temp_usedSettings = temp_usedSettings_1 + temp_usedSettings_2 + temp_usedSettings_3 + temp_usedSettings_4
        self.unusedSettingsIDs = list(set(settingsNames) - set(temp_usedSettings))
        self.unusedSettings, self.unusedSettingsIDs = self._resolveSettingsNames(self._settingsXmlFileNames, self.unusedSettingsIDs)
        if self.settingsFlag and self.settingsExceptions == None:
            self.unusedSettings = self._handleUserExceptions(self.unusedSettings, self.exceptions)
        elif self.settingsExceptions:
            self.unusedSettings = self._handleUserExceptions(self.unusedSettings, self.settingsExceptions)
    
    def _detectDisabledRules(self):
        ruleGroups = self._getFromPolicyFile("ruleGroup")
        self.ruleGroups = [group.get("name") for group in ruleGroups]
        self.disabledRules = [group.get("name") for group in ruleGroups if group.get("enabled") == "false"]
        rules = self._getFromPolicyFile("rule")
        self.rules = [rule.get("name") for rule in rules]
        for rule in rules:
            if rule.get("enabled") == "false":
                self.disabledRules.append(rule.get("name"))
        if self.ruleFlag and self.ruleExceptions == None:
            self.disabledRules = self._handleUserExceptions(self.disabledRules, self.exceptions)
        elif self.ruleExceptions:
            self.disabledRules = self._handleUserExceptions(self.disabledRules, self.ruleExceptions)
    
    def _detectUnusedLists(self):
        usedLists = [usedList.get("id") for usedList in self._getFromPolicyFile("listValue") if usedList.get("id") != None]
        listsXmlFileNames = self._getXmlFromDir("lists")
        self.unusedListsIDs = list(set(listsXmlFileNames) - set(usedLists))
        self.unusedLists, self.unusedListsIDs = self._resolveSettingsNames(self._settingsXmlFileNames, self.unusedListsIDs)
        if self.listFlag and self.listExceptions == None:
            self.unusedLists = self._handleUserExceptions(self.unusedLists, self.exceptions)
        elif self.listExceptions:
            self.unusedLists = self._handleUserExceptions(self.unusedLists, self.listExceptions)
        
    def _cleanup(self):
        if path.isfile("cookies.txt"):
            remove("cookies.txt")
        if path.exists("default"):
            rmtree("default")

    def doReport(self):
        if self._policyXmlLoaded:
            self._archiveOldReports()
            self._writeResults("unusedSettings.csv", "Unused Setting Name", self.unusedSettings, self.unusedSettingsIDs)
            self._writeResults("disabledRules.csv", "Disabled Rule Name", self.disabledRules)
            self._writeResults("unusedLists.csv", "Unused List Name", self.unusedLists, self.unusedListsIDs)

    def _writeResults(self, outfile, header, values, ids=None):
        with open(outfile, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            if ids:
                writer.writerow([header, "ID"])
                for entry in zip(values, ids):
                    writer.writerow(entry)
            else:
                writer.writerow([header])
                for row in values:
                    writer.writerow([row])
    
    def _getAttributeValueFromXml(self, PATH):
        settingsFile = ET.parse(PATH)
        return settingsFile.getroot().get("name")

    def _resolveSettingsNames(self, pathsOfxmlFiles, unusedNames):
        # Paths to the files with unused settings
        unusedSettingsPaths = [element for element in pathsOfxmlFiles if any(nazwa in element for nazwa in unusedNames)]
        return [self._getAttributeValueFromXml(cfgPath) for cfgPath in unusedSettingsPaths], [s.split("/")[-1].rstrip(".xml") for s in unusedSettingsPaths]

    def _archiveOldReports(self):
        # handle disabledRules.csv
        mkdir("archivedReports") if not path.isdir("archivedReports") else None
        move("disabledRules.csv", f"archivedReports/{self.stamp}_disabledRules.csv") if path.isfile("disabledRules.csv") else None
        move("unusedSettings.csv", f"archivedReports/{self.stamp}_unusedSettings.csv") if path.isfile("unusedSettings.csv") else None
        move("unusedLists.csv", f"archivedReports/{self.stamp}_unusedLists.csv") if path.isfile("unusedLists.csv") else None

    def _handleUserExceptions(self, items, user_exceptions):
        if user_exceptions != None:
            with open(user_exceptions, "r") as file:
                exceptions = file.read().split("\n")
            for exception in exceptions:
                items = [item for item in items if item.find(exception) == -1]
            return items
        return items
 
    def _fileExists(self, file):
        if not path.isfile(file):
            print(f"{file} - Provided file does not exists!")
            exit()
    
    def _login(self):
        # login
        if self.USERNAME in ("", None):
            print("[*] Please provide a username!")
            exit()
        USER=self.USERNAME
        password = getpass()
        PASS="{}".format(password)
        URL=f"{self.URL}/Konfigurator/REST/login"
        # query parameters
        params = {"userName": USER, "pass": PASS}
        data = urlencode(params).encode('utf-8')
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # opener object init
        opener = build_opener(HTTPSHandler(context=context))
        try:
            response = opener.open(URL, data)
            cookies = response.getheader('Set-Cookie')
        except urllib.error.HTTPError:
            print("[*] Cannot connect to the device. Validate your credentials and check if the device is up.")
            exit()
        # write cookies to the file
        if cookies:
            with open('cookies.txt', 'w') as f:
                f.write(cookies)
        return opener
    
    def _logout(self, opener):
        URL = f"{self.URL}/Konfigurator/REST/logout"
        data = urlencode("").encode('utf-8')
        opener.open(URL, data)
    
    def downloadBackup(self, opener):
        # Load cookies from txt file
        with open('cookies.txt', 'r') as f:
            cookies = f.read().strip()
        opener.addheaders.append(('Cookie', cookies))
        URL = f"{self.URL}/Konfigurator/REST/backup"
        data = urlencode("").encode('utf-8')
        # Download backupfile
        self.FILE = f"{self.stamp}config.backup"
        with open(self.FILE, 'w') as file:
            backup = opener.open(URL, data)
            file.write(backup.read().decode())
        return opener
            
if __name__ == "__main__":
    pass

