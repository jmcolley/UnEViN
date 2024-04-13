import sys
from pathlib import Path
import unreal
import unevin


# --- UTILITY ---
def mkdirIfItDoesntExist(directoryPath):
    if not directoryPath.is_dir():
        directoryPath.mkdir()

def getSceneFromLineNumber(i):
    # For a given line number, find the furthest down scene for which this line is greater than or equal to its first element
    insideScene = ""
    for scene in list(sceneStartingLineMap.keys()):
        if i >= sceneStartingLineMap[scene]:
            insideScene = scene
        else:
            break
    return insideScene


# --- JSON ---
def getGameJSONPath():
    return Path(tempDir / f"{scriptName}_game.json")

def getCharactersJSONPath():
    return Path(tempDir / f"{scriptName}_characters.json")

def getSceneJSONPath(sceneName):
    return Path(tempDir / f"{scriptName}_scene_{sceneName}.json")

def getChoiceGroupJSONPath(sceneName, groupNumber):
    return Path(tempDir / f"{scriptName}_choicegroup_{sceneName}_{groupNumber}.json")

def makeGameJSON():
    jsonPath = getGameJSONPath()
    with open(jsonPath, 'w') as gameJSONFile:
        gameJSONFile.write("[\n")

def makeCharactersJSON():
    jsonPath = getCharactersJSONPath()
    with open(jsonPath, 'w') as charactersJSONFile:
        charactersJSONFile.write("[\n")

def makeSceneJSON(sceneName):
    jsonPath = getSceneJSONPath(sceneName)
    with open(jsonPath, 'w') as sceneJSONFile:
        sceneJSONFile.write("[\n")

def makeChoiceGroupJSON(sceneName, groupNumber):
    jsonPath = getChoiceGroupJSONPath(sceneName, groupNumber)
    with open(jsonPath, 'w') as choicegroupJSONFile:
        choicegroupJSONFile.write("[\n")


# --- UE ---  
def getDTPath(DTType):    
    return f"/Game/{scriptName}/DT_{DTType}_{scriptName}"

def makeDTOrGetExisting(DTType):
    UEDTPath = getDTPath(DTType)
    if unreal.EditorAssetLibrary.does_asset_exist(UEDTPath):
        return unreal.EditorAssetLibrary.load_asset(UEDTPath)
    else:
        return unreal.EditorAssetLibrary.duplicate_asset(f"/UnEViN/Core/DTTemplates/DT_{DTType}_Template", UEDTPath)
    
def getSceneDTPath(sceneName):
    return f"/Game/{scriptName}/Scenes/DT_Scene_{sceneName}"

def getSceneDTAssetPath(sceneName):
    return f"/Script/Engine.DataTable'/Game/{scriptName}/Scenes/DT_Scene_{sceneName}.DT_Scene_{sceneName}'"

def makeSceneDTOrGetExisting(sceneName):
    UESceneDTPath = getSceneDTPath(sceneName)
    if unreal.EditorAssetLibrary.does_asset_exist(UESceneDTPath):
        return unreal.EditorAssetLibrary.load_asset(UESceneDTPath)
    else:
        return unreal.EditorAssetLibrary.duplicate_asset("/UnEViN/Core/DTTemplates/DT_Scene_Template", UESceneDTPath)
    
def getChoiceGroupDTPath(sceneName, groupNumber):
    return f"/Game/{scriptName}/ChoiceGroups/DT_ChoiceGroups_{sceneName}_{groupNumber}"

def getChoiceGroupDTAssetPath(sceneName, groupNumber):
    return f"/Script/Engine.DataTable'/Game/{scriptName}/ChoiceGroups/DT_ChoiceGroups_{sceneName}_{groupNumber}.DT_ChoiceGroups_{sceneName}_{groupNumber}'"

def makeChoiceGroupDTOrGetExisting(sceneName, groupNumber):
    UEChoiceGroupDTPath = getChoiceGroupDTPath(sceneName, groupNumber)
    if unreal.EditorAssetLibrary.does_asset_exist(UEChoiceGroupDTPath):
        return unreal.EditorAssetLibrary.load_asset(UEChoiceGroupDTPath)
    else:
        return unreal.EditorAssetLibrary.duplicate_asset("/UnEViN/Core/DTTemplates/DT_ChoiceGroup_Template", UEChoiceGroupDTPath)

def importGameJSONToDT(gameDT):
    jsonPath = getGameJSONPath()
    with open(jsonPath, 'a+') as gameJSONFile:
        # Need a final ] after all the appending
        gameJSONFile.write("\n]")
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(gameDT, str(jsonPath))    

def importCharactersJSONToDT(charactersDT):
    jsonPath = getCharactersJSONPath()
    with open(jsonPath, 'a+') as charactersJSONFile:
        # Need a final ] after all the appending
        charactersJSONFile.write("\n]")
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(charactersDT, str(jsonPath))    

def importSceneJSONToDT(sceneName):
    jsonPath = getSceneJSONPath(sceneName)
    with open(jsonPath, 'a+') as sceneJSONFile:
        # Need a final ] after all the appending
        sceneJSONFile.write("\n]")
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(sceneDTs[sceneName], str(jsonPath))  

def importChoiceGroupJSONToDT(sceneName, groupNumber):
    jsonPath = getChoiceGroupJSONPath(sceneName, groupNumber)
    with open(jsonPath, 'a+') as choicegroupJSONFile:
        # Need a final ] after all the appending
        choicegroupJSONFile.write("\n]")
    unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(makeChoiceGroupDTOrGetExisting(sceneName, groupNumber), str(jsonPath))   


# --- MAIN IMPORTER SCRIPT ---    
# Establish directories
scriptPath = Path(sys.argv[1])
scriptName = scriptPath.stem
scriptsDir = scriptPath.parent
tempDir = scriptsDir / "temp"
contentDir = Path(sys.argv[2])
importDir = contentDir / scriptName

if not (scriptsDir.is_dir() and scriptPath.is_file()):
    unevin.getQuitter().quitWithError("REQUESTED SCRIPT FILE DOES NOT EXIST")

if not tempDir.is_dir():
    tempDir.mkdir()

if not contentDir.is_dir():
    unevin.getQuitter().quitWithError("GAME FOLDER IS INVALID")

mkdirIfItDoesntExist(importDir)
mkdirIfItDoesntExist(importDir / "Scenes")
mkdirIfItDoesntExist(importDir / "ChoiceGroups")

# Make characters data table, JSON file
charactersDT = makeDTOrGetExisting("Characters")
makeCharactersJSON()
charactersAdded = 0

# First pass to establish scenes and continuers; handle characters
continuerLines = set()
sceneStartingLineMap = {}
with open(scriptPath, 'r') as script:
    i = 0
    unevin.getQuitter().resetLineNumber()
    for line in script:
        i += 1
        unevin.getQuitter().incrementLineNumber()
        if line.startswith("---"):
            name = unevin.cleanseName(line.strip().strip("-"))
            if name is None or len(name) == 0:
                unevin.getQuitter().quitWithError("INVALID SCENE NAME")
            sceneStartingLineMap[name] = i
        if line.startswith("|"):
            continuerLines.add(i)
        # MAKECHAR {char id} {character display name} [{colour}]
        if line.startswith("MAKECHAR"): 
            chunks = unevin.splitOnSpacesOutsideSpeechmarks(line.strip())
            if len(chunks) in [3,4]:
                currentCharacterObject = unevin.Character()
                if unevin.isValidName(chunks[1]):
                    currentCharacterObject.setName(chunks[1])
                else:
                    unevin.getQuitter().quitWithError(f"INVALID CHARACTER NAME FORMATTING ({chunks[1]}) IN 'MAKECHAR'")
                currentCharacterObject.setDisplayName(unevin.trimSpeechMarks(chunks[2]))
                if len(chunks) == 4:
                    if chunks[3].startswith("#") and len(chunks[3]) == 7:
                        currentCharacterObject.setColor(chunks[3].upper())
                    else:
                        unevin.getQuitter().quitWithError(f"INVALID CHARACTER COLOUR FORMATTING ({chunks[3]}) IN 'MAKECHAR'") 
                unevin.appendJSON(currentCharacterObject, getCharactersJSONPath())
                charactersAdded += 1
            else:
                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS SUPPLIED TO 'MAKECHAR' COMMAND. NOTE: THIS COMMAND CANNOT SHARE A LINE WITH OTHER COMMANDS") 


# Make scene data tables, JSON files, and dictionaries
sceneNames = list(sceneStartingLineMap.keys())
if len(sceneNames) < 1:
    unevin.getQuitter().quitWithError("NO SCENES FOUND")
sceneLinesCounter = {}
sceneDTs = {}
for sceneName in sceneNames:
    sceneLinesCounter[sceneName] = 0
    sceneDTs[sceneName] = makeSceneDTOrGetExisting(sceneName)
    makeSceneJSON(sceneName)
scenesToNumberOfChoiceGroupsMap = {}


# Second pass to handle lines inside scenes and append their data to scene JSON files
multilineBuffer = ""
with open(scriptPath, 'r') as script:
    i = 0
    unevin.getQuitter().resetLineNumber()
    for line in script:
        i += 1
        unevin.getQuitter().incrementLineNumber()       
             
        lineContext = getSceneFromLineNumber(i)
        if len(lineContext) == 0:
            # Skip all lines not in a scene
            continue
        

        if (i in sceneStartingLineMap.values()) or (not line.strip()) or (line.startswith("MAKECHAR")):
            # Skip the starting lines of each scene, or blank lines
            continue

        
        multilineBuffer += line
        if i+1 in continuerLines:
            continue

        chunkifiedLine = [unevin.splitOnSpacesOutsideSpeechmarks(chunk.strip()) for chunk in multilineBuffer.strip().split('|')]
        multilineBuffer = ""

        if len(chunkifiedLine) == 0:
            # If chunkification gave us nothing to work with, skip this line
            continue     
        currentLineObject = unevin.UnevinLineOfDialogue()

        lineHasChoices = False
        for chunk in chunkifiedLine:
            if chunk[0] == "ADDCHOICE":
                lineHasChoices = True
        if lineHasChoices:
            scenesToNumberOfChoiceGroupsMap[lineContext] = 1 + scenesToNumberOfChoiceGroupsMap.get(lineContext, 0)
            choiceGroupNumber = scenesToNumberOfChoiceGroupsMap[lineContext]
            makeChoiceGroupJSON(lineContext, choiceGroupNumber)


        for chunk in chunkifiedLine:            
            # INSTANT (alias for TIMED 0)
            if chunk[0] == 'INSTANT':
                if len(chunk) == 1:
                    currentLineObject.setForcedDuration(0)
                else:
                    unevin.getQuitter().quitWithError("'INSTANT' COMMAND DOES NOT TAKE ARGUMENTS")
            

            # TIMED {duration}
            elif chunk[0] == 'TIMED':
                if len(chunk) == 2:
                    if unevin.isANumber(chunk[1]):
                        currentLineObject.setForcedDuration(chunk[1])
                    else:
                        unevin.getQuitter().quitWithError(f"'TIMED' COMMAND'S DURATION ({chunk[1]}) MUST BE A NUMBER")
                else:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'TIMED' COMMAND")
            

            # IF {conditions}
            elif chunk[0] == 'IF':
                if len(chunk) > 1:
                    conditions = ' '.join(chunk[1:])
                    currentLineObject.setActiveConditions(conditions)
                else:
                    unevin.getQuitter().quitWithError("MUST PROVIDE CONDITION ARGUMENT(S) TO 'IF' COMMAND")
            

            # VAR {varname} {variable transformer} [{modification}]
            elif chunk[0] == 'VAR':
                if len(chunk) in [3,4]:
                    varName, persistent = unevin.persistentCheckAndStrip(chunk[1])
                    if unevin.isValidName(varName):
                        modifier = 0
                        if len(chunk) > 3:
                            modifier = unevin.trimSpeechMarks(chunk[3])
                        currentLineObject.addVariableTransform(varName, persistent, chunk[2], modifier)
                    else:
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({varName}) FOR VARIABLE NAME")
                else:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'VAR' COMMAND")
            

            # SET {varname} {modification} (basically an alias for VAR with {variable transformer} set to '=')
            elif chunk[0] == 'SET':
                if len(chunk) == 3:
                    varName, persistent = unevin.persistentCheckAndStrip(chunk[1])
                    if unevin.isValidName(varName):
                        modifier = unevin.trimSpeechMarks(chunk[2])
                        currentLineObject.addVariableTransform(varName, persistent, "=", modifier)
                    else:
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({varName}) FOR VARIABLE NAME")
                else:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'SET' COMMAND")
            

            # INCREMENT/DECREMENT {varname} [BY {modification}] (basically an alias for VAR with {variable transformer} set to '+' or '-')
            elif chunk[0] in ['INCREMENT', 'DECREMENT']:
                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["BY"])
                transformerName = '-' if chunk[0] == 'DECREMENT' else '+'
                modifier = 1

                if not len(subchunks[0]) == 2:
                    unevin.getQuitter().quitWithError(f"WRONG NUMBER OF ARGUMENTS FOR '{chunk[0]}' COMMAND")
                else:
                    varName, persistent = unevin.persistentCheckAndStrip(subchunks[0][1])
                    if not unevin.isValidName(varName):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({varName}) FOR VARIABLE NAME")
                  
                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'BY':
                            if len(subchunk) == 2:
                                modifier = subchunk[1]
                            else:
                                unevin.getQuitter().quitWithError(f"WRONG NUMBER OF ARGUMENTS FOR 'BY' SUBCOMMAND OF '{chunk[0]}'")
                        else:
                            unevin.getQuitter().quitWithError(f"INVALID SUBCOMMAND SUPPLIED TO '{chunk[0]}'")     
                        currentLineObject.addVariableTransform(varName, persistent, transformerName, modifier)


            # EVENT {event name} [{additional data}]
            elif chunk[0] == 'EVENT':
                if len(chunk) in [2,3]:
                    if unevin.isValidName(chunk[1]):
                        addData = 0
                        if len(chunk) > 2:
                            addData = unevin.trimSpeechMarks(chunk[2])
                        currentLineObject.addExternalEvent(chunk[1], addData)
                    else:
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({chunk[1]}) FOR EXTERNAL EVENT NAME")
                else:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'EVENT' COMMAND")
            

            # SHOWSPRITE {sprite name} {displayableID} [AT {front or back}] [POS {position coords}] [SIZE {scale coords}] [TRANS {duration} {interp}] [INITPOS {relative position coords}] [INITSIZE {relative scale coords}]
            elif chunk[0] == 'SHOWSPRITE':
                order = 'Front'
                tx = ty = itx = ity = '0'
                sx = sy = isx = isy = '1'
                duration = '0'
                interp = "Linear"

                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["AT", "POS", "SIZE", "TRANS", "INITPOS", "INITSIZE"])
                
                if not len(subchunks[0]) == 3:
                    unevin.getQuitter().quitWithError("INVALID ARGUMENTS FOR 'SHOWSPRITE' COMMAND")
                else:               
                    spriteName = subchunks[0][1]
                    if not unevin.isValidName(spriteName):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({spriteName}) FOR SPRITE NAME")      
                    displayableID = subchunks[0][2]
                    if not unevin.isValidName(displayableID):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({displayableID}) FOR DISPLAYABLE ID")       
                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'AT':
                            if len(subchunk) == 2:
                                order = subchunk[1]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'AT' SUBCOMMAND OF 'SHOWSPRITE'")
                        elif subchunk[0] == 'POS':
                            if len(subchunk) == 3:
                                tx, ty = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'POS' SUBCOMMAND OF 'SHOWSPRITE'")
                        elif subchunk[0] == 'INITPOS':
                            if len(subchunk) == 3:
                                itx, ity = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'INITPOS' SUBCOMMAND OF 'SHOWSPRITE'")
                        elif subchunk[0] == 'SIZE':
                            if len(subchunk) == 3:
                                sx, sy = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'SIZE' SUBCOMMAND OF 'SHOWSPRITE'")
                        elif subchunk[0] == 'INITSIZE':
                            if len(subchunk) == 3:
                                isx, isy = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'FROMSIZE' SUBCOMMAND OF 'SHOWSPRITE'")
                        elif subchunk[0] == 'TRANS':
                            if len(subchunk) == 3:
                                duration = subchunk[1]
                                interp = subchunk[2]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'TRANS' SUBCOMMAND OF 'SHOWSPRITE'")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'SHOWSPRITE'")                    
                for shouldBeNumber in [tx, ty, itx, ity, sx, sy, isx, isy, duration]:
                    if not unevin.isANumber(shouldBeNumber):
                        unevin.getQuitter().quitWithError(f"INVALID NUMBER {shouldBeNumber} SUPPLIED TO 'SHOWSPRITE' COMMAND")                
                currentLineObject.addSpriteToShow(spriteName, displayableID, order, tx, ty, sx, sy, duration, itx, ity, isx, isy, interp)
            

            # CHANGESPRITE {sprite name} [AT {front or back}] [POS {position coords}] [SIZE {scale coords}] [TRANS {duration} {interp}]
            elif chunk[0] == 'CHANGESPRITE':
                changeOrder = "none"
                changePos = False
                ntx = nty = '0'
                changeSize = False
                nsx = nsy = '1'
                duration = '0'
                interp = "Linear"

                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["AT", "POS", "SIZE", "TRANS"])
                
                if not len(subchunks[0]) == 2:
                    unevin.getQuitter().quitWithError("INVALID ARGUMENTS FOR 'CHANGESPRITE' COMMAND")
                else:
                    spriteName = subchunks[0][1]
                    if not unevin.isValidName(spriteName):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({spriteName}) FOR SPRITE NAME")
                
                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'AT':
                            if len(subchunk) == 2:
                                changeOrder = subchunk[1]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'AT' SUBCOMMAND OF 'CHANGESPRITE'")
                        elif subchunk[0] == 'POS':
                            if len(subchunk) == 3:
                                ntx, nty = subchunk[1:]
                                changePos = True
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'POS' SUBCOMMAND OF 'CHANGESPRITE'")
                        elif subchunk[0] == 'SIZE':
                            if len(subchunk) == 3:
                                nsx, nsy = subchunk[1:]
                                changeSize = True
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'SIZE' SUBCOMMAND OF 'CHANGESPRITE'")
                        elif subchunk[0] == 'TRANS':
                            if len(subchunk) == 3:
                                duration = subchunk[1]
                                interp = subchunk[2]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'TRANS' SUBCOMMAND OF 'CHANGESPRITE'")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'CHANGESPRITE'")
                    
                for shouldBeNumber in [ntx, nty, nsx, nsy, duration]:
                    if not unevin.isANumber(shouldBeNumber):
                        unevin.getQuitter().quitWithError(f"INVALID NUMBER {shouldBeNumber} SUPPLIED TO 'CHANGESPRITE' COMMAND")
                
                currentLineObject.addSpriteToChange(spriteName, changeOrder, changePos, ntx, nty, changeSize, nsx, nsy, duration, interp)
            

            # HIDESPRITE {sprite name} [TRANS {duration} {interp}] [FINALPOS {relative position coords}] [FINALSIZE {relative scale coords}]
            elif chunk[0] == 'HIDESPRITE':
                ftx=fty='0'
                fsx=fsy='1'
                duration='0'
                interp="Linear"

                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["TRANS", "FINALPOS", "FINALSIZE"])
                
                if not len(subchunks[0]) == 2:
                    unevin.getQuitter().quitWithError("INVALID ARGUMENTS FOR 'HIDESPRITE' COMMAND")
                else:               
                    spriteName = subchunks[0][1]
                    if not unevin.isValidName(spriteName):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({spriteName}) FOR SPRITE NAME")      

                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'FINALPOS':
                            if len(subchunk) == 3:
                                ftx, fty = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'FINALPOS' SUBCOMMAND OF 'HIDESPRITE'")
                        elif subchunk[0] == 'FINALSIZE':
                            if len(subchunk) == 3:
                                fsx, fsy = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'FINALSIZE' SUBCOMMAND OF 'HIDESPRITE'")
                        elif subchunk[0] == 'TRANS':
                            if len(subchunk) == 3:
                                duration = subchunk[1]
                                interp = subchunk[2]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'TRANS' SUBCOMMAND OF 'HIDESPRITE'")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'HIDESPRITE'")                    
                for shouldBeNumber in [ftx, fty, fsx, fsy, duration]:
                    if not unevin.isANumber(shouldBeNumber):
                        unevin.getQuitter().quitWithError(f"INVALID NUMBER {shouldBeNumber} SUPPLIED TO 'HIDESPRITE' COMMAND")                
                currentLineObject.addSpriteToHide(spriteName, duration, interp, ftx, fty, fsx, fsy)
            

            # SHOWMODEL {model name} {mesh group ID} [ATTACH {attach tag}] [ORIGIN {origin tag}] [POS {position coords}] [ROT {rotation coords}] [SIZE {scale coords}] [TRANS {duration} {interp}] [INITPOS {relative position coords}] [INITROT {relative scale coords}] [INITSIZE {relative scale coords}]
            elif chunk[0] == 'SHOWMODEL':
                attachTag=originTag=""
                tx=ty=tz=rx=ry=rz=itx=ity=itz=irx=iry=irz='0'
                sx=sy=sz=isx=isy=isz='1'
                duration='0'
                interp="Linear"
                
                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["ATTACH", "ORIGIN", "POS", "ROT", "SIZE", "TRANS", "INITPOS", "INITROT", "INITSIZE"])
                
                if not len(subchunks[0]) == 3:
                    unevin.getQuitter().quitWithError("INVALID ARGUMENTS FOR 'SHOWMODEL' COMMAND")
                else:               
                    modelName = subchunks[0][1]
                    if not unevin.isValidName(modelName):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({modelName}) FOR MODEL NAME")      
                    meshGroup = subchunks[0][2]
                    if not unevin.isValidName(meshGroup):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({meshGroup}) FOR MESH GROUP ID")       
                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'ATTACH':
                            if len(subchunk) == 2:
                                attachTag = subchunk[1]
                                if not unevin.isValidName(attachTag):
                                    unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({attachTag}) FOR ATTACHMENT TAG")    
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'ATTACH' SUBCOMMAND OF 'SHOWMODEL'")
                        elif subchunk[0] == 'ORIGIN':
                            if len(subchunk) == 2:
                                originTag = subchunk[1]
                                if not unevin.isValidName(originTag):
                                    unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({originTag}) FOR ORIGIN TAG")    
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'ORIGIN' SUBCOMMAND OF 'SHOWMODEL'")
                        elif subchunk[0] == 'POS':
                            if len(subchunk) == 4:
                                tx, ty, tz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'POS' SUBCOMMAND OF 'SHOWMODEL'")
                        elif subchunk[0] == 'INITPOS':
                            if len(subchunk) == 4:
                                itx, ity, itz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'INITPOS' SUBCOMMAND OF 'SHOWMODEL'")
                        elif subchunk[0] == 'ROT':
                            if len(subchunk) == 4:
                                rx, ry, rz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'ROT' SUBCOMMAND OF 'SHOWMODEL'")
                        elif subchunk[0] == 'INITROT':
                            if len(subchunk) == 4:
                                irx, iry, irz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'INITROT' SUBCOMMAND OF 'SHOWMODEL'")
                        elif subchunk[0] == 'SIZE':
                            if len(subchunk) == 4:
                                sx, sy, sz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'SIZE' SUBCOMMAND OF 'SHOWMODEL'")
                        elif subchunk[0] == 'INITSIZE':
                            if len(subchunk) == 4:
                                isx, isy, isz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'FROMSIZE' SUBCOMMAND OF 'SHOWMODEL'")
                        elif subchunk[0] == 'TRANS':
                            if len(subchunk) == 3:
                                duration = subchunk[1]
                                interp = subchunk[2]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'TRANS' SUBCOMMAND OF 'SHOWMODEL'")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'SHOWMODEL'")                    
                for shouldBeNumber in [tx,ty,tz,rx,ry,rz,itx,ity,itz,irx,iry,irz,sx,sy,sz,isx,isy,isz,duration]:
                    if not unevin.isANumber(shouldBeNumber):
                        unevin.getQuitter().quitWithError(f"INVALID NUMBER {shouldBeNumber} SUPPLIED TO 'SHOWMODEL' COMMAND") 
                currentLineObject.addModelToShow(modelName, meshGroup, attachTag, originTag, tx, ty, tz, rx, ry, rz, sx, sy, sz, duration, interp, itx, ity, itz, irx, iry, irz, isx, isy, isz)
            

            # CHANGEMODEL {model name} [ATTACH {attach tag}] [ORIGIN {origin tag}] [POS {position coords}] [ROT {rotation coords}] [SIZE {scale coords}] [TRANS {duration} {interp}]
            elif chunk[0] == 'CHANGEMODEL':
                changeAttach=False
                newAttachTag=moveToTag=""
                duration='0'
                interp="Linear"
                ntx=nty=ntz=nrx=nry=nrz='0'
                nsx=nsy=nsz='1'
                
                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["ATTACH", "ORIGIN", "POS", "ROT", "SIZE", "TRANS"])
                
                if not len(subchunks[0]) == 2:
                    unevin.getQuitter().quitWithError("INVALID ARGUMENTS FOR 'CHANGEMODEL' COMMAND")
                else:               
                    modelName = subchunks[0][1]
                    if not unevin.isValidName(modelName):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({modelName}) FOR MODEL NAME")         
                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'ATTACH':
                            if len(subchunk) == 2:
                                newAttachTag = subchunk[1]
                                if not unevin.isValidName(newAttachTag):
                                    unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({newAttachTag}) FOR ATTACHMENT TAG")    
                                changeAttach = True
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'ATTACH' SUBCOMMAND OF 'CHANGEMODEL'")
                        elif subchunk[0] == 'ORIGIN':
                            if len(subchunk) == 2:
                                moveToTag = subchunk[1]
                                if not unevin.isValidName(moveToTag):
                                    unevin.getQuitter().quitWithError(f"INVALID FORMATTING {moveToTag} FOR ORIGIN TAG")    
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'ORIGIN' SUBCOMMAND OF 'CHANGEMODEL'")
                        elif subchunk[0] == 'POS':
                            if len(subchunk) == 4:
                                ntx, nty, ntz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'POS' SUBCOMMAND OF 'CHANGEMODEL'")
                        elif subchunk[0] == 'ROT':
                            if len(subchunk) == 4:
                                nrx, nry, nrz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'ROT' SUBCOMMAND OF 'CHANGEMODEL'")
                        elif subchunk[0] == 'SIZE':
                            if len(subchunk) == 4:
                                nsx, nsy, nsz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'SIZE' SUBCOMMAND OF 'CHANGEMODEL'")
                        elif subchunk[0] == 'TRANS':
                            if len(subchunk) == 3:
                                duration = subchunk[1]
                                interp = subchunk[2]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'TRANS' SUBCOMMAND OF 'CHANGEMODEL'")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'CHANGEMODEL'")                    
                for shouldBeNumber in [duration, ntx, nty, ntz, nrx, nry, nrz, nsx, nsy, nsz]:
                    if not unevin.isANumber(shouldBeNumber):
                        unevin.getQuitter().quitWithError(f"INVALID NUMBER {shouldBeNumber} SUPPLIED TO 'CHANGEMODEL' COMMAND") 
                currentLineObject.addModelToChange(modelName, changeAttach, newAttachTag, moveToTag, duration, interp, ntx, nty, ntz, nrx, nry, nrz, nsx, nsy, nsz)
            

            # HIDEMODEL {model name} [FINALPOS {position coords}] [FINALROT {rotation coords}] [FINALSIZE {scale coords}] [TRANS {duration} {interp}]
            elif chunk[0] == 'HIDEMODEL':
                duration='0'
                interp='Linear'
                ftx=fty=ftz=frx=fry=frz='0'
                fsx=fsy=fsz='1'
                
                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["FINALPOS", "FINALROT", "FINALSIZE", "TRANS"])
                
                if not len(subchunks[0]) == 2:
                    unevin.getQuitter().quitWithError("INVALID ARGUMENTS FOR 'HIDEMODEL' COMMAND")
                else:               
                    modelName = subchunks[0][1]
                    if not unevin.isValidName(modelName):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({modelName}) FOR MODEL NAME")         
                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'FINALPOS':
                            if len(subchunk) == 4:
                                ftx, fty, ftz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'FINALPOS' SUBCOMMAND OF 'HIDEMODEL'")
                        elif subchunk[0] == 'FINALROT':
                            if len(subchunk) == 4:
                                frx, fry, frz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'FINALROT' SUBCOMMAND OF 'HIDEMODEL'")
                        elif subchunk[0] == 'FINALSIZE':
                            if len(subchunk) == 4:
                                fsx, fsy, fsz = subchunk[1:]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'FINALSIZE' SUBCOMMAND OF 'HIDEMODEL'")
                        elif subchunk[0] == 'TRANS':
                            if len(subchunk) == 3:
                                duration = subchunk[1]
                                interp = subchunk[2]
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'TRANS' SUBCOMMAND OF 'HIDEMODEL'")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'HIDEMODEL'")                    
                for shouldBeNumber in [duration, ftx, fty, ftz, frx, fry, frz, fsx, fsy, fsz]:
                    if not unevin.isANumber(shouldBeNumber):
                        unevin.getQuitter().quitWithError(f"INVALID NUMBER {shouldBeNumber} SUPPLIED TO 'CHANGEMODEL' COMMAND") 
                currentLineObject.addModelToHide(modelName, duration, interp, ftx, fty, ftz, frx, fry, frz, fsx, fsy, fsz)


            # ANIM {model name} {anim name} [{loop}]
            elif chunk[0] == 'ANIM':
                if len(chunk) in [3,4]:
                    modelName = chunk[1]
                    animName = chunk[2]
                    loop = False
                    if unevin.isValidName(modelName) and unevin.isValidName(animName):
                        if len(chunk) == 4:
                            loop = (chunk[3].lower().startswith("t") or chunk[3] == '1' or chunk[3] == "loop")
                        currentLineObject.addAnimation(modelName, animName, loop)
                    else:
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING FOR MODEL OR ANIMATION NAME")

                else:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'ANIM' COMMAND")


            # DLOGBOX {show or hide} [{anim} {duration}]
            elif chunk[0] == 'DLOGBOX':
                if len(chunk) in [2,4]:
                    direction = chunk[1].lower()
                    if not direction in ['show', 'hide']:
                        unevin.getQuitter().quitWithError("'DLOGBOX' COMMAND MUST HAVE FIRST ARGUMENT 'show' OR 'hide'")
                    anim = 'fade'
                    duration = '0'
                    if len(chunk) == 4:
                        anim = chunk[2].lower().replace(' ','')
                        duration = chunk[3]
                        if not unevin.isANumber(duration):
                            unevin.getQuitter().quitWithError(f"'DLOGBOX' DURATION ({duration}) MUST BE A NUMBER")
                    currentLineObject.addDialogueBoxAnimation(direction, duration, anim)
                else:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'DLOGBOX' COMMAND")


            # LEVEL {new level name}
            elif chunk[0] == 'LEVEL':
                if len(chunk) != 2:
                    newlevelname = chunk[1]
                    if not unevin.isValidName(newlevelname):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({newlevelname}) FOR LEVEL NAME IN 'LEVEL' COMMAND")
                    currentLineObject.setLevelChange(newlevelname)
                else:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'LEVEL' COMMAND")


            # CAM {tag} [TRANS {transition type} {time} [{exponent}]]
            elif chunk[0] == 'CAM':              
                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["TRANS"])
                if not len(subchunks[0]) == 2:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'CAM' COMMAND")    

                newCamTag = subchunks[0][1]
                if not unevin.isValidName(newCamTag):
                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({newCamTag}) FOR CAMERA TAG IN 'CAM' COMMAND")
                else:                
                    currentLineObject.setViewpointChange(newCamTag)

                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'TRANS':
                            if len(subchunk) in [3,4]:
                                blendType = subchunk[1].lower()
                                blendTime = subchunk[2]
                                if not unevin.isANumber(blendTime):
                                    unevin.getQuitter().quitWithError(f"'CAM' TRANSITION BLEND TIME ({blendTime}) MUST BE A NUMBER")
                                currentLineObject.setViewpointTransitionType(blendType)
                                currentLineObject.setViewpointTransitionBlendTime(blendTime)
                                blendExponent = 3
                                if len(subchunk) > 3:
                                    blendExponent = subchunk[3]
                                    if not unevin.isANumber(blendExponent):
                                        unevin.getQuitter().quitWithError(f"'CAM' TRANSITION BLEND EXPONENT ({blendExponent}) MUST BE A NUMBER")
                                currentLineObject.setViewpointTransitionBlendExponent(blendExponent)
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'TRANS' SUBCOMMAND OF 'CAM' COMMAND")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'CAM'")     


            # ADDCHOICE {body text} [JUMP/CALL {optional destination scene name}] [IF {conditions}] [ACTIVEIF {conditions}] [COLOR {text colours} {button colours}]
            elif chunk[0] == 'ADDCHOICE':
                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["JUMP", "CALL", "IF", "ACTIVEIF", "COLOR"])

                if len(subchunks[0]) != 2:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'ADDCHOICE' COMMAND")
                
                currentChoiceObject = unevin.UnevinChoice()
                currentChoiceObject.setBody(unevin.trimSpeechMarks(chunk[1]))

                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] in ['JUMP', 'CALL']:
                            if not len(subchunk) == 2:
                                unevin.getQuitter().quitWithError(f"WRONG NUMBER OF ARGUMENTS FOR '{subchunk[0]}' SUBCOMMAND OF 'ADDCHOICE'")
                            else:
                                choiceDestSceneName = unevin.cleanseName(subchunk[1])
                                if choiceDestSceneName in sceneNames:
                                    currentChoiceObject.setDestination(getSceneDTAssetPath(choiceDestSceneName), (subchunk[0] == "CALL"))
                                else:
                                    unevin.getQuitter().quitWithError("INVALID SCENE NAME SPECIFIED FOR 'ADDCHOICE' DESTINATION")
                        elif subchunk[0] == 'IF':
                            if len(subchunk) > 1:
                                conditions = ' '.join(subchunk[1:])
                                currentChoiceObject.setVisibleConditions(conditions)
                            else:
                                unevin.getQuitter().quitWithError("MUST PROVIDE CONDITION ARGUMENT(S) TO 'IF' SUBCOMMAND OF 'ADDCHOICE' COMMAND")
                        elif subchunk[0] == 'ACTIVEIF':
                            if len(subchunk) > 1:
                                conditions = ' '.join(subchunk[1:])
                                currentChoiceObject.setActiveConditions(conditions)
                            else:
                                unevin.getQuitter().quitWithError("MUST PROVIDE CONDITION ARGUMENT(S) TO 'ACTIVEIF' SUBCOMMAND OF 'ADDCHOICE' COMMAND")
                        elif subchunk[0] == 'COLOR':
                            if len(subchunk) == 9:
                                tr, tg, tb, ta, br, bg, bb, ba = subchunk[1:]              
                                for shouldBeNumber in [tr, tg, tb, ta, br, bg, bb, ba]:
                                    if not unevin.isANumber(shouldBeNumber):
                                        unevin.getQuitter().quitWithError(f"INVALID NUMBER ({shouldBeNumber}) SUPPLIED TO 'COLOR' SUBCOMMAND OF 'ADDCHOICE' COMMAND")      
                                currentChoiceObject.setOverrideColours(tr, tg, tb, ta, br, bg, bb, ba)
                            else:
                                unevin.getQuitter().quitWithError("MUST PROVIDE EIGHT ARGUMENTS (TEXT RGBA, BUTTON RGBA) TO 'COLOR' SUBCOMMAND OF 'ADDCHOICE' COMMAND")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'ADDCHOICE'")     

                unevin.appendJSON(currentChoiceObject, getChoiceGroupJSONPath(lineContext, choiceGroupNumber))


            # INPUT {variableName} [DEFAULT {default value} [{show default}]] [PROCESSVIA {string processors}]
            elif chunk[0] == 'INPUT':
                default = ""
                showDefault = False
                processors = []

                subchunks = unevin.makeSubListsAtGivenStrings(chunk, ["DEFAULT", "PROCESSVIA"])

                if len(subchunks[0]) != 2:
                    unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'INPUT' COMMAND")
                else:
                    varName, persistent = unevin.persistentCheckAndStrip(subchunks[0][1])

                if len(subchunks) > 1:
                    for subchunk in subchunks[1:]:
                        if subchunk[0] == 'DEFAULT':
                            if len(subchunk) in [2,3]:
                                default = subchunk[1]
                                if len(subchunk) == 3:
                                    showDefault = (subchunk[2].lower().startswith('t') or subchunk[2] == '1' or subchunk[2] == 'show')
                            else:
                                unevin.getQuitter().quitWithError("WRONG NUMBER OF ARGUMENTS FOR 'DEFAULT' SUBCOMMAND OF 'INPUT' COMMAND")
                        elif subchunk[0] == 'PROCESSVIA':
                            if len(subchunk) > 1:
                                for stringprocessor in subchunk[1:]:
                                    if unevin.isValidName(stringprocessor):
                                        processors.append(stringprocessor)
                                    else:
                                        unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({stringprocessor}) FOR STRING PROCESSOR NAME IN 'PROCESSVIA' SUBCOMMAND OF 'INPUT'")
                            else:
                                unevin.getQuitter().quitWithError("MUST PROVIDE AT LEAST ONE STRING PROCESSOR NAME TO 'PROCESSVIA' SUBCOMMAND OF 'INPUT'")
                        else:
                            unevin.getQuitter().quitWithError("INVALID SUBCOMMAND SUPPLIED TO 'INPUT'")                    
                currentChoiceObject.setPlayerInput(varName, persistent, default, showDefault, processors)


            # JUMP/CALL {destination scene name}
            elif chunk[0] in ['JUMP', 'CALL']:
                if len(chunk) == 2:
                    destSceneName = unevin.cleanseName(chunk[1])
                    if destSceneName in sceneNames:
                        currentLineObject.setDestination(getSceneDTAssetPath(destSceneName), (chunk[0] == "CALL"))
                    else:
                        unevin.getQuitter().quitWithError(f"INVALID SCENE NAME SPECIFIED FOR '{chunk[0]}' DESTINATION")
                else:
                    unevin.getQuitter().quitWithError(f"WRONG NUMBER OF ARGUMENTS FOR '{chunk[0]}' COMMAND")


            # [SAY] [{character name}] {body text}        
            else:
                if (chunk[-1].startswith(r'"') and chunk[-1].endswith(r'"')) and ((chunk[0] == "SAY" and len(chunk) in [2,3]) or (len(chunk) == 2 and unevin.isValidName(chunk[0])) or (len(chunk) == 1)):
                    currentLineObject.setBody(chunk[-1])
                    if len(chunk) > 1 and chunk[-2] != 'SAY':
                        if unevin.isValidName(chunk[-2]):
                            currentLineObject.setCharacter(chunk[-2])
                        else:                        
                            unevin.getQuitter().quitWithError(f"INVALID FORMATTING ({chunk[-2]}) FOR CHARACTER NAME")
                else:
                    unevin.getQuitter().quitWithError(f"UNRECOGNISED COMMAND '{chunk[0]}'")



        if lineHasChoices:
            importChoiceGroupJSONToDT(lineContext, choiceGroupNumber)
            currentLineObject.setChoiceGroup(getChoiceGroupDTAssetPath(lineContext, choiceGroupNumber))         

        unevin.appendJSON(currentLineObject, getSceneJSONPath(lineContext))
        sceneLinesCounter[lineContext] += 1

for sceneName in sceneLinesCounter.keys():
    if sceneLinesCounter[sceneName] < 1:
        unevin.getQuitter().quitWithError(f"SCENE {sceneName} HAD NO VALID LINES")    

# Import JSON files to Data Tables
if charactersAdded > 0:
    importCharactersJSONToDT(charactersDT)
for sceneName in list(sceneDTs.keys()): 
    importSceneJSONToDT(sceneName)

# Create game DT etc if they don't exist
if not unreal.EditorAssetLibrary.does_asset_exist(getDTPath("Game")):
    makeDTOrGetExisting("Characters")
    makeDTOrGetExisting("Displayables")
    makeDTOrGetExisting("MeshGroups")
    makeDTOrGetExisting("Animations")
    makeDTOrGetExisting("ConditionClasses")
    makeDTOrGetExisting("StringProcessors")
    makeDTOrGetExisting("VariableTransformers")
    gameDT = makeDTOrGetExisting("Game")
    makeGameJSON()
    unevin.dumpJSONAndAppend({
		"Name": "game",
		"DisplayName": f"{scriptName}",
        "InitialDestination":
		{
			"Scene": getSceneDTAssetPath(list(sceneStartingLineMap.keys())[0]),
			"RowName": "None"
		},
		"Characters": f"/Script/Engine.DataTable'/Game/{scriptName}/DT_Characters_{scriptName}.DT_Characters_{scriptName}'",
		"Displayables": f"/Script/Engine.DataTable'/Game/{scriptName}/DT_Displayables_{scriptName}.DT_Displayables_{scriptName}'",
		"MeshGroups": f"/Script/Engine.DataTable'/Game/{scriptName}/DT_MeshGroups_{scriptName}.DT_MeshGroups_{scriptName}'",
		"Animations": f"/Script/Engine.DataTable'/Game/{scriptName}/DT_Animations_{scriptName}.DT_Animations_{scriptName}'",
		"ConditionClasses": f"/Script/Engine.DataTable'/Game/{scriptName}/DT_ConditionClasses_{scriptName}.DT_ConditionClasses_{scriptName}'",
		"StringProcessors": f"/Script/Engine.DataTable'/Game/{scriptName}/DT_StringProcessors_{scriptName}.DT_StringProcessors_{scriptName}'",
		"VariableTransformers": f"/Script/Engine.DataTable'/Game/{scriptName}/DT_VariableTransformers_{scriptName}.DT_VariableTransformers_{scriptName}'"
	}, getGameJSONPath())
    importGameJSONToDT(gameDT)