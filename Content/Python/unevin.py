import json, random, string, re
import unreal

def generateRandomName():
    return "".join([random.choice(string.digits + string.ascii_uppercase) for i in range(16)])

def cleanseName(inputString):
    return re.sub(r'[^\x30-\x39\x41-\x5A\x61-\x7A\x5F\x2D]',r'', inputString.replace(" ","-"))

def dumpJSONAndAppend(thingToDump, filePathToAppend):
    with open(filePathToAppend, 'a') as outputFile:
        json.dump(thingToDump, outputFile, indent="\t")   
        
def getSceneTablePath(scriptName, destinationScene):
    return f"/Script/Engine.DataTable'/Game/{scriptName}/Scenes/DT_Scene_{destinationScene}.DT_Scene_{destinationScene}'"
        
def getChoiceGroupTablePath(scriptName, choiceGroupName):
    return f"/Script/Engine.DataTable'/Game/{scriptName}/ChoiceGroup/DT_Choices_{choiceGroupName}.DT_Choices_{choiceGroupName}'"

class LineOfDialog:
    def __init__(self):
        self.dictionary = {
            "Name": "NewRow",
            "Type": "SAY",
            "CharName": "None",
            "Body": "",
            "Destination":
            {
                "Scene": "None",
                "RowName": "None"
            },
            "DestinationJumpIsCall": False,
            "Conditions": [],
            "VariablesToSet": [],
            "ChoiceGroup": "None",
            "InputPrompt":
            {
                "VariableToSet":
                {
                    "Name": "None",
                    "Value": "",
                    "Persistent": False
                },
                "ShowDefault": False,
                "StripToAlphanumericASCII": False,
                "StripSpaces": False,
                "StripASCIINumbers": False,
                "StripASCIILetters": False,
                "ConvertToCase": "Unchanged"
            }
        }
        self.dictionary["Name"] = generateRandomName()
        
    def getDict(self):
        return self.dictionary
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.dictionary, outputFilePath)
        
    def setRowName(self, rowName):
        self.dictionary["Name"] = rowName
        
    def setCharacter(self, characterName):
        self.dictionary["CharName"] = characterName
        
    def setBody(self, body):
        self.dictionary["Body"] = body
        
    def setType(self, lineType):
        self.dictionary["Type"] = lineType
        
    def setChoiceGroup(self, scriptName, choiceGroupName):
        self.dictionary["ChoiceGroup"] = getChoiceGroupTablePath(scriptName, choiceGroupName)
        
    def setDestination(self, scriptName, destinationScene):
        self.dictionary["Destination"] = {"Scene": getSceneTablePath(scriptName, destinationScene), "RowName": "None"}
                
    def setDestinationRaw(self, rawDestination):
        self.dictionary["Destination"] = {"Scene": rawDestination, "RowName": "None"}
        
    def setIsCall(self, isCall):
        self.dictionary["DestinationJumpIsCall"] = isCall
        
        
        
class Choice:
    def __init__(self):
        self.dictionary = {
            "Name": "NewRow",
            "Body": "",
            "Destination":
            {
                "Scene": "None",
                "RowName": "None"
            },
            "DestinationJumpIsCall": False,
            "VisibleConditions": [],
            "ActiveConditions": []
        }
        self.dictionary["Name"] = generateRandomName()
        
    def getDict(self):
        return self.dictionary
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.dictionary, outputFilePath)
        
    def setBody(self, body):
        self.dictionary["Body"] = body
                
    def setDestination(self, scriptName, destinationScene):
        self.dictionary["Destination"] = {"Scene": getSceneTablePath(scriptName, destinationScene), "RowName": "None"}
        
    def setIsCall(self, isCall):
        self.dictionary["DestinationJumpIsCall"] = isCall
        
        
class Character:
    def __init__(self):
        self.dictionary = {
            "Name": "NewRow",
            "DisplayName": "",
            "Color":
            {
                "B": 0,
                "G": 0,
                "R": 0,
                "A": 0
            }
        }
        self.dictionary["Name"] = generateRandomName()
        
    def getDict(self):
        return self.dictionary
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.dictionary, outputFilePath)
    
    def setName(self, name):
        self.dictionary["Name"] = name
    
    def setDisplayName(self, dname):
        self.dictionary["DisplayName"] = dname
    
    def setColor(self, color):
        color = color.replace("#","")
        self.dictionary["Color"] = {"R": str(int(color[:2], 16)), "G": str(int(color[2:4], 16)), "B": str(int(color[4:6], 16)), "A": 255}

#def setActiveVN(vnName):
#    startSceneLineObject = LineOfDialog()
#    startSceneLineObject.setName("beginGame")
#    startSceneLineObject.setType("INSTANT")
#    startSceneLineObject.setDestinationRaw(f"/Script/Engine.DataTable'/Game/{vnName}/DT_Scene_Init_{vnName}.DT_Scene_Init_{vnName}'")
#    with open("startscene_temp.json", )
#    startTable = unreal.EditorAssetLibrary.load_asset("/Game/UnEViN/Core/DT_Start")
#    unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(startTable, startSceneCSVLine)

def addTableToCharactersCompTable(charTable):
    characterCompTable = unreal.EditorAssetLibrary.load_asset("/Game/UnEViN/Core/DT_Comp_Characters")
    characterTables = characterCompTable.get_editor_property("ParentTables")
    if not charTable in characterTables:
        characterTables.insert(0, charTable)
    characterCompTable.set_editor_property("ParentTables", characterTables, notify_mode = unreal.PropertyAccessChangeNotifyMode.ALWAYS)
    characterCompTable.modify()