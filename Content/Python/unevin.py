import json, random, string, re
import unreal

def generateRandomName():
    return "".join([random.choice(string.digits + string.ascii_uppercase) for i in range(16)])

def trimSpeechMarks(inputString):
    startIndex = 0
    endIndex = None
    if inputString.startswith('"'):
        startIndex = 1
    if inputString.endswith('"'):
        endIndex = -1
    return inputString[startIndex : endIndex]

def cleanseName(inputString):
    return re.sub(r'[^\x30-\x39\x41-\x5A\x61-\x7A\x5F\x2D]',r'', inputString.replace(" ","-")) #Removes all characters besides ASCII letters, numbers, hyphen and underscore; and changes spaces to hyphens

def isANumber(inputString):
    for char in trimSpeechMarks(inputString):
        if char not in r'.0123456789':
            return False
    return True

def dumpJSONAndAppend(thingToDump, filePathToAppend):
    with open(filePathToAppend, 'a') as outputFile:
        json.dump(thingToDump, outputFile, indent="\t")   

def appendJSON(object, filePath):
    if object is not None:
        with open(filePath, 'a+') as JSONFile:
            if filePath.stat().st_size > 5:  #If it's too big to have just '[' in it, we need a prefixing comma
                JSONFile.write(",\n")
        object.appendJSONToFile(filePath)
        
def getSceneTablePath(scriptName, destinationScene):
    destinationScene = cleanseName(destinationScene)
    return f"/Script/Engine.DataTable'/Game/{scriptName}/Scenes/DT_Scene_{destinationScene}.DT_Scene_{destinationScene}'"
        
def getChoiceGroupTablePath(scriptName, choiceGroupName):
    return f"/Script/Engine.DataTable'/Game/{scriptName}/ChoiceGroup/DT_Choices_{choiceGroupName}.DT_Choices_{choiceGroupName}'"

def addTableToCharactersCompTable(charTable):
    characterCompTable = unreal.EditorAssetLibrary.load_asset("/Game/UnEViN/Core/DT_Comp_Characters")
    characterTables = characterCompTable.get_editor_property("ParentTables")
    if not charTable in characterTables:
        characterTables.insert(0, charTable)
    characterCompTable.set_editor_property("ParentTables", characterTables, notify_mode = unreal.PropertyAccessChangeNotifyMode.ALWAYS)
    characterCompTable.modify()

def setActiveVN(vnName, tempJSONLocation):
    startSceneLineObject = LineOfDialog()
    startSceneLineObject.setRowName("beginGame")
    startSceneLineObject.setType("INSTANT")
    startSceneLineObject.setDestination(Destination.from_raw(f"/Script/Engine.DataTable'/Game/{vnName}/DT_Scene_Init_{vnName}.DT_Scene_Init_{vnName}'"))
    with open(tempJSONLocation, 'w') as startJSONFile:
        startJSONFile.write("[\n")
    appendJSON(startSceneLineObject, tempJSONLocation)
    with open(tempJSONLocation, 'a+') as startJSONFile:
        startJSONFile.write("]")
    startTable = unreal.EditorAssetLibrary.load_asset("/Game/UnEViN/Core/DT_Start")
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(startTable, str(tempJSONLocation))



class UnevinStruct:        
    def getDict(self):
        return self.dictionary
    
    
class Variable(UnevinStruct):
    def __init__(self):
        self.dictionary = {
            "Name": "None",
            "Value": "",
            "Persistent": False
        }        
        
    def setName(self, varName):
        self.dictionary["Name"] = varName
        
    def setValue(self, varValue):
        self.dictionary["Value"] = varValue
        
    def setPersistent(self, persistent):
        self.dictionary["Persistent"] = persistent
    
    @classmethod
    def from_properties_explicitpersistence(cls, varName, varValue, persistent):
        var = cls()
        var.setName(varName)
        var.setValue(varValue)
        var.setPersistent(persistent)
        return var
    
    @classmethod
    def from_properties(cls, varName, varValue):
        persistent = False
        if trimSpeechMarks(varName).startswith("persistent."):
            persistent = True
            varName = varName.replace("persistent.", "")
        return cls.from_properties_explicitpersistence(varName, varValue, persistent)
        
        
class Condition(UnevinStruct):
    def __init__(self):
        self.dictionary = {
            "ConditionType": "ExactlyEqualTo",
            "Variable": Variable().getDict()
        }
        
    def setType(self, conType):
        self.dictionary["ConditionType"] = conType
        
    def setTypeFromSymbol(self, symbol):
        conType = "ExactlyEqualTo"
        if symbol == r'!=' or symbol == r'=/=' or symbol == r'=\=':
            conType = "DoesNotEqual"
        elif symbol == r'<=' or symbol == r'=<':
            conType = "LessThanOrEqualTo"
        elif symbol == r'<':
            conType = "StrictlyLessThan"
        elif symbol == r'>=' or symbol == r'=>':
            conType = "GreaterThanOrEqualTo"
        elif symbol == r'>':
            conType = "StrictlyGreaterThan"
        self.setType(conType)
    
    def setVar(self, var):
        self.dictionary["Variable"] = var.getDict()
    
    @classmethod
    def from_properties_and_symbol(cls, varName, condSymbol, varValue):
        cond = cls()
        cond.setVar(Variable.from_properties(varName, varValue))
        cond.setTypeFromSymbol(condSymbol)
        return cond


class Destination(UnevinStruct):
    def __init__(self):
        self.dictionary = {
            "Scene": "None",
            "RowName": "None"
        }
    
    def setScene(self, scene):
        self.dictionary["Scene"] = scene
    
    def setRowName(self, rowName):
        self.dictionary["RowName"] = rowName
    
    @classmethod
    def from_script(cls, scriptName, destinationScene):
        dest = cls()
        dest.setScene(getSceneTablePath(scriptName, destinationScene))
        return dest
    
    @classmethod
    def from_raw(cls, rawDestination):
        dest = cls()
        dest.setScene(rawDestination)
        return dest    
        

class TransitionSettings(UnevinStruct):
    def __init__(self):
        self.dictionary = {
            "BlendType": "Linear",
            "BlendTime": 0,
            "BlendExponent": 1.2,
            "LockOutgoingCamera": False
        }
    
    def setBlendType(self, blendType):
        self.dictionary["BlendType"] = blendType
    
    def setBlendTime(self, blendTime):
        self.dictionary["BlendTime"] = blendTime
    
    def setBlendExponent(self, blendExponent):
        self.dictionary["BlendExponent"] = blendExponent
    
    def setLockOutgoingCamera(self, lockOutgoingCamera):
        self.dictionary["LockOutgoingCamera"] = lockOutgoingCamera
    
    @classmethod
    def from_type_and_time(cls, blendType, blendTime):
        trans = cls()
        trans.setBlendType(blendType)
        trans.setBlendTime(blendTime)
        return trans    


class Viewpoint(UnevinStruct):   
    def __init__(self):
        self.dictionary = {
            "LevelName": "None",
            "CameraTagName": "None",
            "TransitionSettings": TransitionSettings().getDict()            
        }     
    
    def setLevelName(self, levelName):
        self.dictionary["LevelName"] = levelName
    
    def setCameraTagName(self, cameraTagName):
        self.dictionary["CameraTagName"] = cameraTagName
    
    def setTransitionSettings(self, transSetting):
        self.dictionary["TransitionSettings"] = transSetting.getDict()
        
        
class InputPrompt(UnevinStruct):
    def __init__(self):
        self.variable = Variable()
        self.dictionary = {
            "VariableToSet": self.variable.getDict(),
            "ShowDefault": False,
            "StripToAlphanumericASCII": False,
            "StripSpaces": False,
            "StripASCIINumbers": False,
            "StripASCIILetters": False,
            "ConvertToCase": "Unchanged"
        }

    def getDict(self):
        self.dictionary["VariableToSet"] = self.variable.getDict()
        return self.dictionary
        
    def getVariableToSet(self):
        return self.variable
        
    def setVariableToSet(self, variableToSet):
        self.variable = variableToSet
        
    def setShowDefault(self, showDefault):
        self.dictionary["ShowDefault"] = showDefault
        
    def setStripToAlphanumericASCII(self, stripToAlphanumericASCII):
        self.dictionary["StripToAlphanumericASCII"] = stripToAlphanumericASCII
        
    def setStripSpaces(self, stripSpaces):
        self.dictionary["StripSpaces"] = stripSpaces
        
    def setStripASCIINumbers(self, stripASCIINumbers):
        self.dictionary["StripASCIINumbers"] = stripASCIINumbers
        
    def setStripASCIILetters(self, stripASCIILetters):
        self.dictionary["StripASCIILetters"] = stripASCIILetters
        
    def setConvertToCase(self, case):
        self.dictionary["ConvertToCase"] = case
        
        
class LineOfDialog(UnevinStruct):
    def __init__(self):
        self.destination = Destination()
        self.inputprompt = InputPrompt()
        self.viewpoint = Viewpoint()
        self.dictionary = {
            "Name": generateRandomName(),
            "Type": "SAY",
            "CharName": "None",
            "Body": "",
            "Destination": self.destination.getDict(),
            "DestinationJumpIsCall": False,
            "Conditions": [],
            "VariablesToSet": [],
            "ChoiceGroup": "None",
            "InputPrompt": self.inputprompt.getDict(),
            "Viewpoint": self.viewpoint.getDict()
        }

    def getDict(self):
        self.dictionary["Destination"] = self.destination.getDict()
        self.dictionary["InputPrompt"] = self.inputprompt.getDict()
        self.dictionary["Viewpoint"] = self.viewpoint.getDict()
        return self.dictionary
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.getDict(), outputFilePath)
        
    def setRowName(self, rowName):
        self.dictionary["Name"] = rowName
        
    def setCharacter(self, characterName):
        self.dictionary["CharName"] = characterName
        
    def setBody(self, body):
        self.dictionary["Body"] = body
        
    def getType(self):
        return self.dictionary["Type"]
        
    def setType(self, lineType):
        self.dictionary["Type"] = lineType
        
    def getDestination(self):
        return self.destination

    def setDestination(self, newDestination):
        self.destination = newDestination

    def setIsCall(self, isCall):
        self.dictionary["DestinationJumpIsCall"] = isCall
        
    def addCondition(self, conditionToAdd):
        self.dictionary["Conditions"].append(conditionToAdd.getDict())
        
    def addVariableToSet(self, variableToSet):
        self.dictionary["VariablesToSet"].append(variableToSet.getDict())
        
    def setChoiceGroup(self, scriptName, choiceGroupName):
        self.dictionary["ChoiceGroup"] = getChoiceGroupTablePath(scriptName, choiceGroupName)
        
    def getInputPrompt(self):
        return self.inputprompt
        
    def setInputPrompt(self, newInputPrompt):
        self.inputprompt = newInputPrompt
                
    def getViewpoint(self):
        return self.viewpoint
                
    def setViewpoint(self, newViewpoint):
        self.viewpoint = newViewpoint
        
    def setViewTransitionSettings(self, transSetting):
        self.viewpoint.setTransitionSettings(transSetting)
        self.updateViewpoint()
               
        
class Choice(UnevinStruct):
    def __init__(self):
        self.destination = Destination()
        self.dictionary = {
            "Name": generateRandomName(),
            "Body": "",
            "Destination": self.destination.getDict(),
            "DestinationJumpIsCall": False,
            "VisibleConditions": [],
            "ActiveConditions": []
        }

    def getDict(self):
        self.dictionary["Destination"] = self.destination.getDict()
        return self.dictionary
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.getDict(), outputFilePath)
        
    def setBody(self, body):
        self.dictionary["Body"] = body
                
    def setDestination(self, destination):
        self.destination = destination

    def setIsCall(self, isCall):
        self.dictionary["DestinationJumpIsCall"] = isCall
        
    def addCondition(self, choiceConditionType, conditionToAdd):
        if 'active' in choiceConditionType.lower():
            self.dictionary["ActiveConditions"].append(conditionToAdd.getDict())
        else:
            self.dictionary["VisibleConditions"].append(conditionToAdd.getDict())
        
        
class Character(UnevinStruct):
    def __init__(self):
        self.dictionary = {
            "Name": generateRandomName(),
            "DisplayName": "",
            "Color":
            {
                "B": 0,
                "G": 0,
                "R": 0,
                "A": 0
            }
        }
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.getDict(), outputFilePath)
    
    def setName(self, name):
        self.dictionary["Name"] = name
    
    def setDisplayName(self, dname):
        self.dictionary["DisplayName"] = dname
    
    def setColor(self, color):
        color = color.replace("#","")
        self.dictionary["Color"] = {"R": str(int(color[:2], 16)), "G": str(int(color[2:4], 16)), "B": str(int(color[4:6], 16)), "A": 255}