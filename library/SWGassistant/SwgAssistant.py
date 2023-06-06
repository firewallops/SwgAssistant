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
    def __init__(self) -> None:
        self._baseCfgPath = ""
        self._settingsXmlFileNames = ""
        self._settingsNames = ""
        self._policyXmlLoaded = False
        self.exceptions = ""
        self.listExceptions = ""
        self.URL = ""
        self.FILE = ""
        self.stamp = datetime.strftime(datetime.now(), "%Y_%m_%d-%H_%M")
        self.USERNAME = ""
    
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
        if self.exceptions is not None:        
            self._fileExists(self.exceptions)  
            if self.listExceptions != True:
                print("[*] [Warning] Don't know where to apply the exceptions! Skipping.")      
        args = argparse.Namespace(backupfile=configXmlFile, outpath='.', v=False)
        SwgUnpack(args)
        self._get_baseCfgPath()
        if self._baseCfgPath != "":
            self._detectUnusedSettings()
            self._detectDisabledRules()
            self._detectUnusedLists()
            self._cleanup()

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
        self.unusedSettings = list(((set(settingsNames) - set(temp_usedSettings_1)) - set(temp_usedSettings_2)) - set(temp_usedSettings_3))
        self.unusedSettings = self._resolveSettingsNames(self._settingsXmlFileNames, self.unusedSettings)
    
    def _detectDisabledRules(self):
        ruleGroups = self._getFromPolicyFile("ruleGroup")
        self.ruleGroups = [group.get("name") for group in ruleGroups]
        self.disabledRules = [group.get("name") for group in ruleGroups if group.get("enabled") == "false"]
        rules = self._getFromPolicyFile("rule")
        self.rules = [rule.get("name") for rule in rules]
        for rule in rules:
            if rule.get("enabled") == "false":
                self.disabledRules.append(rule.get("name"))
    
    def _detectUnusedLists(self):
        usedLists = [usedList.get("id") for usedList in self._getFromPolicyFile("listValue") if usedList.get("id") != None]
        listsXmlFileNames = self._getXmlFromDir("lists")
        self.unusedLists = list(set(listsXmlFileNames) - set(usedLists))
        self.unusedLists = self._resolveSettingsNames(self._settingsXmlFileNames, self.unusedLists)
        if self.listExceptions:
            self.unusedLists = self._handleUserExceptions(self.unusedLists)
        
    def _cleanup(self):
        if path.isfile("cookies.txt"):
            remove("cookies.txt")
        if path.exists("default"):
            rmtree("default")

    def doReport(self):
        if self._policyXmlLoaded:
            self._archiveOldReports()
            self._writeResults("unusedSettings.csv", "Unused Setting Name", self.unusedSettings)
            self._writeResults("disabledRules.csv", "Disabled Rule Name", self.disabledRules)
            self._writeResults("unusedLists.csv", "Unused List Name", self.unusedLists)

    def _writeResults(self, outfile, header, values):
        with open(outfile, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([header])
            for row in values:
                writer.writerow([row])
    
    def _getAttributeValueFromXml(self, PATH):
        settingsFile = ET.parse(PATH)
        return settingsFile.getroot().get("name")

    def _resolveSettingsNames(self, pathsOfxmlFiles, unusedNames):
        # Paths to the files with unused settings
        unusedSettingsPaths = [element for element in pathsOfxmlFiles if any(nazwa in element for nazwa in unusedNames)]
        return [self._getAttributeValueFromXml(cfgPath) for cfgPath in unusedSettingsPaths]

    def _archiveOldReports(self):
        # handle disabledRules.csv
        mkdir("archivedReports") if not path.isdir("archivedReports") else None
        move("disabledRules.csv", f"archivedReports/{self.stamp}_disabledRules.csv") if path.isfile("disabledRules.csv") else None
        move("unusedSettings.csv", f"archivedReports/{self.stamp}_unusedSettings.csv") if path.isfile("unusedSettings.csv") else None
        move("unusedLists.csv", f"archivedReports/{self.stamp}_unusedLists.csv") if path.isfile("unusedLists.csv") else None

    def _handleUserExceptions(self, items):
        if self.exceptions != None:
            with open(self.exceptions, "r") as file:
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

