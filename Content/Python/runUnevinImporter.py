import sys, re, string
from pathlib import Path
import unreal
import unevin


subCommands = ['CALL', 'JUMP', 'CAM', 'LEVEL', 'SET', 'IF', 'PROMPT_DEFAULT', 'PROMPT_SANITISE']
choiceSubCommands = ['CALL', 'JUMP', 'VISIBLEIF', 'ACTIVEIF']

def chunkify(inList, separators):
    separators.append('END')
    inList.append('END')
    chunks = []
    currentChunk = []
    for item in inList:
        if item in separators and len(currentChunk) != 0:
            chunks.append(currentChunk)
            currentChunk = []
        currentChunk.append(item)
    return chunks


unevinScriptFilePath = Path(sys.argv[1])
unevinScriptFolder = unevinScriptFilePath.parent
unevinScriptName = unevinScriptFilePath.stem


def findBlocksInFile(filePath, delimiters):
    with open(filePath, 'r') as script:
        delimitersDict = {}
        for delimiter in delimiters:
            delimitersDict[delimiter] = [False, None, []]
        i = 0
        for line in script:
            i += 1
            for delimiter in delimiters:
                if line.startswith(delimiter*3):
                    if not delimitersDict[delimiter][0]:
                        name = unevin.cleanseName(line.strip().strip(delimiter))
                        if name is None or len(name) == 0:
                            name = unevin.generateRandomName()
                        delimitersDict[delimiter][1] = [name, i]
                    else:
                        delimitersDict[delimiter][1].append(i)
                        delimitersDict[delimiter][2].append(delimitersDict[delimiter][1])
                        delimitersDict[delimiter][1] = None
                    delimitersDict[delimiter][0] = not delimitersDict[delimiter][0]
    if True in [delimitersDict[delimiter][0] for delimiter in delimiters]:
        print("ERROR: Some block never ended properly")
        return False
    else:
        return {delimiter: delimitersDict[delimiter][2] for delimiter in delimiters}
        

def splitLineUp(line):
    splitLine = line.strip().replace("\n","").split(" ")
    insideString = False
    newLine = []
    for item in splitLine:            
        if not insideString:
            newLine.append(item.replace(r'\"', '"'))
        else: 
            newLine[-1] += " " + item.replace(r'\"', '"')  
            
        if item.replace(r'\"', '').count('"') % 2 != 0:
            insideString = not insideString
    splitLine = newLine
    return splitLine
        
def getLineContext(lineNumber):
    context = {'label': None, 'choiceGroup': None}
    for labelName, startLine, endLine in labels:
        if lineNumber >= startLine and lineNumber <= endLine:
            context['label'] = labelName
            break
    for choiceGroupName, startLine, endLine in choiceGroups: 
        if lineNumber >= startLine and lineNumber <= endLine:
            context['choiceGroup'] = choiceGroupName
            break
    return context

def parseLineToLineOfDialogObject(line, lineNum):
    if line[0] not in string.ascii_letters + string.digits + '"_': # Check if the first character is anything invalid
        return None
    else:
        splitLine = splitLineUp(line)        
        print(splitLine)

        currentLineObject = unevin.LineOfDialog()

        if splitLine[0] == 'INSTANT':
            currentLineObject = parseLineToLineOfDialogObject("SAY" + line[7:], lineNum)
            currentLineObject.setType("INSTANT")        
        elif splitLine[0] == 'PROMPT':
            currentLineObject = parseLineToLineOfDialogObject("SAY" + line[(7 + len(splitLine[1])):], lineNum)
            currentLineObject.setType("PROMPT")
            currentLineObject.getInputPrompt().getVariableToSet().setName(splitLine[1])
        elif splitLine[0] == 'FORK':
            if "BY" in splitLine:
                currentLineObject = parseLineToLineOfDialogObject("SAY" + line[4:], lineNum)
                currentLineObject.setChoiceGroup(unevinScriptName, splitLine[splitLine.index("BY")+1])    
                currentLineObject.setType("FORK")               
            else:
                mostRecentlyDefinedChoiceGroup = [cg for cg in choiceGroups if cg[1] == lineNum+1]
                if len(mostRecentlyDefinedChoiceGroup) == 1:
                    currentLineObject = parseLineToLineOfDialogObject(line + f" BY {mostRecentlyDefinedChoiceGroup[0][0]}", lineNum)
                else:
                    print(f"ERROR: No choice group defined for FORK at line {lineNum}!")
                    return None             
        elif splitLine[0] in subCommands:
            return parseLineToLineOfDialogObject(f'INSTANT None "" ' + line, lineNum)
        elif splitLine[0] == 'SAY':
            if len(splitLine) < 3 or (splitLine[1].startswith('"') and splitLine[1].endswith('"')):
                currentLineObject = parseLineToLineOfDialogObject("SAY None " + line[4:], lineNum)
            elif (splitLine[2].startswith('"') and splitLine[2].endswith('"')):
                currentLineObject.setCharacter(splitLine[1])
                currentLineObject.setBody(unevin.trimSpeechMarks(splitLine[2]))

                chunks = chunkify(splitLine[3:], subCommands)
                
                for chunk in chunks:   
                    print(chunk)             
                    if chunk[0] == "CALL":
                        currentLineObject.setIsCall(True)
                        chunk[0] = "JUMP"

                    if chunk[0] == "JUMP":
                        if (len(chunk) == 2):
                            currentLineObject.setDestination(unevin.Destination.from_script(unevinScriptName, unevin.trimSpeechMarks(chunk[1])))
                        else:
                            print(f"ERROR: Malformed CALL/JUMP at line {lineNum}!")
                    elif chunk[0] == "CAM":
                        if (len(chunk) == 2 or len(chunk) == 4):
                            currentLineObject.getViewpoint().setCameraTagName(unevin.cleanseName(chunk[1]))
                            if (len(chunk) == 4):
                                if (chunk[2] in ['Linear', 'Cubic', 'EaseIn', 'EaseOut', 'EaseInAndOut', 'NoBlending']) and unevin.isANumber(chunk[3]):
                                    currentLineObject.getViewpoint().setTransitionSettings(unevin.TransitionSettings.from_type_and_time(chunk[2], float(unevin.trimSpeechMarks(chunk[3]))))
                        else:
                            print(f"ERROR: Malformed CAM at line {lineNum}!")
                    elif chunk[0] == "LEVEL":
                        if (len(chunk) == 2):
                            currentLineObject.getViewpoint().setLevelName(unevin.cleanseName(chunk[1]))       
                        else:
                            print(f"ERROR: Malformed LEVEL at line {lineNum}!")
                    elif chunk[0] == "SET":
                        if (len(chunk) == 3):
                            currentLineObject.addVariableToSet(unevin.Variable.from_properties(unevin.cleanseName(chunk[1]), unevin.trimSpeechMarks(chunk[2])))   
                        else:
                            print(f"ERROR: Malformed SET at line {lineNum}!")
                    elif chunk[0] == "IF":
                        if (len(chunk) == 4):
                            currentLineObject.addCondition(unevin.Condition.from_properties_and_symbol(unevin.cleanseName(chunk[1]), unevin.trimSpeechMarks(chunk[2]), unevin.trimSpeechMarks(chunk[3])))
                        else:
                            print(f"ERROR: Malformed IF at line {lineNum}!")
                    elif chunk[0] == "PROMPT_DEFAULT":
                        if (len(chunk) == 3):
                            currentLineObject.getInputPrompt().getVariableToSet().setValue(chunk[1])
                            currentLineObject.getInputPrompt().setShowDefault(chunk[2])
                            print(currentLineObject.getInputPrompt().getDict())
                        else:
                            print(f"ERROR: Malformed PROMPT_DEFAULT at line {lineNum}!")                    
                    elif chunk[0] == "PROMPT_SANITISE":
                        if (len(chunk) == 6):
                            currentLineObject.getInputPrompt().setStripToAlphanumericASCII(chunk[1])
                            currentLineObject.getInputPrompt().setStripSpaces(chunk[2])
                            currentLineObject.getInputPrompt().setStripASCIINumbers(chunk[3])
                            currentLineObject.getInputPrompt().setStripASCIILetters(chunk[4])
                            currentLineObject.getInputPrompt().setConvertToCase(chunk[5])
                            print(currentLineObject.getInputPrompt().getDict())
                        else:
                            print(f"ERROR: Malformed PROMPT_SANITISE at line {lineNum}!")  
            else:
                print(f"ERROR: Malformed line at line {lineNum}!")
                return None  
        else:
            return parseLineToLineOfDialogObject("SAY " + line, lineNum)  
                        
        return currentLineObject   

def parseLineToChoiceObject(line, lineNum):
    splitLine = splitLineUp(line)
    if len(splitLine) >= 1 and splitLine[0].startswith('"'):
        currentChoiceObject = unevin.Choice()
        currentChoiceObject.setBody(unevin.trimSpeechMarks(splitLine[0]))
        chunks = chunkify(splitLine[1:], choiceSubCommands)
        for chunk in chunks:
            if chunk[0] == 'CALL':
                currentChoiceObject.setIsCall(True)
                chunk[0] = "JUMP"

            if chunk[0] == 'JUMP':
                if (len(chunk) == 2):
                    currentChoiceObject.setDestination(unevin.Destination.from_script(unevinScriptName, unevin.trimSpeechMarks(chunk[1])))
                else:
                    print(f"ERROR: Malformed CALL/JUMP at line {lineNum}!")
            elif chunk[0] in ['VISIBLEIF', 'ACTIVEIF']:
                if (len(chunk) == 4):
                    currentChoiceObject.addCondition(chunk[0], unevin.Condition.from_properties_and_symbol(unevin.cleanseName(chunk[1]), unevin.trimSpeechMarks(chunk[2]), unevin.trimSpeechMarks(chunk[3])))
                else:
                    print(f"ERROR: Malformed VISIBLEIF/ACTIVEIF at line {lineNum}!")

        return currentChoiceObject
    else:
        print(f"ERROR: Malformed choice at line {lineNum}!")
        return None
    
def parseLineToCharacterObject(line, lineNum):
    splitLine = splitLineUp(line)
    if splitLine[0] == 'MAKECHAR' and len(splitLine) >= 3:
        currentCharacterObject = unevin.Character()
        currentCharacterObject.setName(splitLine[1])
        currentCharacterObject.setDisplayName(splitLine[2][1:-1])
        if len(splitLine) == 4:
            currentCharacterObject.setColor(splitLine[3])
        return currentCharacterObject
    else:
        print(f"ERROR: Malformed MAKECHAR at line {lineNum}!")
        return None

                 
#First pass to establish label and choice group blocks in the script.
blocksByDelimiter = findBlocksInFile(unevinScriptFilePath, ('-', '*'))
labels = blocksByDelimiter['-']
choiceGroups = blocksByDelimiter['*']


#Make all our data tables so we don't have trouble referencing them later, and store references to them.
#Each item in the dicts is a pair where the key is the name of the item, value 0 is a reference to its UE5 datatable,
#and value 1 is an (initially empty) list of my own objects that will be converted to JSON later to populate it.
scenesDict = {}
for labelName, startLine, endLine in labels: 
    scenesDict[labelName] = (unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Scene_Empty", f"/Game/{unevinScriptName}/Scenes/DT_Scene_{labelName}"), unevinScriptFolder/f"{unevinScriptName}_Scene_{labelName}_temp.json")
    with open(scenesDict[labelName][1], 'w') as sceneJSONFile:
        sceneJSONFile.write("[\n")
        
choiceGroupsDict = {}        
for choiceGroupName, startLine, endLine in choiceGroups: 
    choiceGroupsDict[choiceGroupName] = (unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Choices_Empty", f"/Game/{unevinScriptName}/ChoiceGroup/DT_Choices_{choiceGroupName}"), unevinScriptFolder/f"{unevinScriptName}_Choices_{choiceGroupName}_temp.json")
    with open(choiceGroupsDict[choiceGroupName][1], 'w') as choicesJSONFile:
        choicesJSONFile.write("[\n")   
        
characters = (unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Characters_Empty", f"/Game/{unevinScriptName}/DT_Characters_{unevinScriptName}"), unevinScriptFolder/f"{unevinScriptName}_Characters_temp.json")    
with open(characters[1], 'w') as charactersJSONFile:
    charactersJSONFile.write("[\n")   


#Second pass to populate lists in dict with objects    
with open(unevinScriptFilePath, 'r') as script:
    lineNum = 0
    for line in script: 
        lineNum += 1
        context = getLineContext(lineNum)
        if context['choiceGroup'] is not None: #Dealing with lines which are in choice group definition blocks
            choiceObject = parseLineToChoiceObject(line, lineNum)
            unevin.appendJSON(choiceObject, choiceGroupsDict[context['choiceGroup']][1])
        elif context['label'] is not None: #Dealing with lines that are in scene blocks
            lineObject = parseLineToLineOfDialogObject(line, lineNum)
            unevin.appendJSON(lineObject, scenesDict[context['label']][1])
        elif len(line.strip()) > 0: #Dealing with lines outside of any blocks (i.e. character definitions)
            characterObject = parseLineToCharacterObject(line, lineNum)
            unevin.appendJSON(characterObject, characters[1])
            
 
#Put the final ] characters into the JSON files we've generated and import them to Unreal
for scene in scenesDict:
    with open(scenesDict[scene][1], 'a+') as sceneJSONFile:
        sceneJSONFile.write("]")
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(scenesDict[scene][0], str(scenesDict[scene][1]))    
    
for choicegroup in choiceGroupsDict:
    with open(choiceGroupsDict[choicegroup][1], 'a+') as choicesJSONFile:
        choicesJSONFile.write("]")
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(choiceGroupsDict[choicegroup][0], str(choiceGroupsDict[choicegroup][1]))  
    
with open(characters[1], 'a+') as charactersJSONFile:
    charactersJSONFile.write("]")
unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(characters[0], str(characters[1]))
unevin.addTableToCharactersCompTable(characters[0])


#Create init scene to point to from game start config
initJSONPath = unevinScriptFolder/f"{unevinScriptName}_Scene_Init_{unevinScriptName}_temp.json"
with open(initJSONPath, 'w') as initJSONFile:
    initJSONFile.write("[\n")
initSceneLineObject = unevin.LineOfDialog()
initSceneLineObject.setRowName("beginGame")
initSceneLineObject.setType("INSTANT")
initSceneLineObject.setDestination(unevin.Destination.from_script(unevinScriptName, labels[0][0]))
unevin.appendJSON(initSceneLineObject, initJSONPath)
with open(initJSONPath, 'a+') as initJSONFile:
    initJSONFile.write("]")
initSceneTable = unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Scene_Empty", f"/Game/{unevinScriptName}/DT_Scene_Init_{unevinScriptName}")
unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(initSceneTable, str(initJSONPath))

#Point to init scene from game start config
unevin.setActiveVN(unevinScriptName, unevinScriptFolder/f"{unevinScriptName}_CoreStart_temp.json")


#TODO: reimplement cleaning up of JSON files with a million checks
#tempJSONFilePath.unlink()