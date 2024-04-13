import json, random, string, re, sys
import unreal



# --- LINE COUNTING --- 
class LineCounterQuitter:
    def __init__(self):
        self.linenumber = 0
    
    def resetLineNumber(self):
        self.linenumber = 0
    
    def incrementLineNumber(self):
        self.linenumber += 1
    
    def getLineNumber(self):
        return self.linenumber

    def quitWithError(self, errMess):    
        print(f"UNEVIN ERROR: {errMess} (WHILE IMPORTING LINE {self.linenumber})")
        sys.exit()

quitter = LineCounterQuitter()

def getQuitter():
    return quitter




# --- UTILITY ---
def generateRandomName():
    # Generates a random string of 16 characters
    return "".join([random.choice(string.digits + string.ascii_uppercase) for i in range(16)])

def trimSpeechMarks(inputString):
    # Removes leading and trailing speech marks
    startIndex = 0
    endIndex = None
    if inputString.startswith('"'):
        startIndex = 1
    if inputString.endswith('"'):
        endIndex = -1
    return inputString[startIndex : endIndex]

def cleanseName(inputString):
    # Converts to lowercase, removes all characters besides ASCII letters, numbers, hyphen and underscore; and changes spaces to hyphens
    return re.sub(r'[^\x30-\x39\x41-\x5A\x61-\x7A\x5F\x2D]',r'', inputString.replace(" ","-")).lower() 

def isValidName(inputString):
    # Would cleanseName make any changes? If so, we're not a valid name
    return (inputString == cleanseName(inputString))

def isANumber(inputString):
    inputString = str(inputString)
    # Returns yes if input string is numeric (allowing decimals and negatives)
    numberOfPeriods = 0
    for char in trimSpeechMarks(inputString):
        if char not in r'-.0123456789':
            return False
        elif char is '.':
            numberOfPeriods += 1
    if numberOfPeriods > 1:
            return False
    return True
        
def splitOnSpacesOutsideSpeechmarks(string):
    # Splits a chunk on every space but keeps stuff inside speechmarks as a single element
    splitString = string.split(" ")
    insideSpeech = False
    newString = []
    for item in splitString:            
        if not insideSpeech:
            newString.append(item.replace(r'\"', '"'))
        else: 
            newString[-1] += " " + item.replace(r'\"', '"')              
        if item.replace(r'\"', '').count('"') % 2 != 0:
            insideSpeech = not insideSpeech
    return newString

def makeSubListsAtGivenStrings(listToSublistify, givenStringsList):
    sublistifiedOutput = []
    currentSublist = []
    for item in listToSublistify:
        if item in givenStringsList:
            if len(currentSublist) > 0:
                sublistifiedOutput.append(currentSublist)
                currentSublist = []
        currentSublist.append(item)    
    if len(currentSublist) > 0:
        sublistifiedOutput.append(currentSublist)
        currentSublist = []
    return sublistifiedOutput
                



# --- HANDLE CONDITIONS (CNF) ---
def splitConditionString(conditionString):
    splitCondString = []

    currentAppend = ""
    i = 0
    insideSpeech = False
    while i < len(conditionString):
        char = conditionString[i]
        if char == r'"':
            insideSpeech = not insideSpeech
            currentAppend += r'"'
            i += 1   
        elif insideSpeech:
            currentAppend += char
            i += 1   
        elif char == '(':
            closeBracketLoc = -1
            depth = 0
            for j in range(i+1, len(conditionString)):
                if conditionString[j] == '(':
                    depth += 1
                elif conditionString[j] == ')':
                    if depth == 0:
                        closeBracketLoc = j
                        break
                    else:
                        depth -= 1
            if closeBracketLoc == -1:
                quitter.quitWithError("BRACKET OPENED BUT NEVER CLOSED IN CONDITION")
                return
            else:
                if len(currentAppend) > 0:
                    splitCondString.append(currentAppend)
                currentAppend = ""
                splitCondString.append(splitConditionString(conditionString[i+1:closeBracketLoc]))
                i = closeBracketLoc+1
        elif conditionString[i:i+5] == ' AND ':
            if len(currentAppend) > 0:
                splitCondString.append(currentAppend)     
                currentAppend = ""       
            splitCondString.append('AND')
            i += 5
        elif conditionString[i:i+4] == ' OR ':
            if len(currentAppend) > 0:
                splitCondString.append(currentAppend)    
                currentAppend = ""               
            splitCondString.append('OR')
            i += 4
        else:
            currentAppend += char
            i += 1    
    if len(currentAppend) > 0:
        splitCondString.append(currentAppend)
    return splitCondString
        

def typifyConditionString(splitCondString):
    if len(splitCondString) == 1:
        return (['AND', splitCondString[0]])
    else:
        typedCondString = ['']

        for item in splitCondString:
            if item in ['OR', 'AND']:
                if len(typedCondString[0]) == 0:
                    typedCondString[0] = item
                elif typedCondString[0] != item:
                    quitter.quitWithError("AMBIGUOUS BRACKETING IN CONDITION")
                    return
            else:
                if isinstance(item, str):
                    typedCondString.append([item])
                else:                    
                    typedCondString.append(item)
        for i in range(1, len(typedCondString)):
            typedCondString[i] = typifyConditionString(typedCondString[i])
        
        if typedCondString[0] == 'OR':
            singleClause = True
            for subitem in typedCondString[1:]:
                if (len(subitem) != 2) or (subitem[0] not in ['AND', 'NOT']):
                    singleClause = False
            if singleClause:
                return ['AND', typedCondString]
            
        return typedCondString
    
def getVariablesFromConditionString(conditionString):
    return conditionString.replace('(', '').replace(')', '').replace(' AND ', '||DELIMIT||').replace(' OR ', '||DELIMIT||').split('||DELIMIT||')

def evaluateTypifiedCondString(typedCondString, truthDict):
    type = typedCondString[0]
    for item in typedCondString[1:]:
        if isinstance(item, str):
            value = truthDict.get(item, "ERROR")
            if value not in [True, False]:
                quitter.quitWithError("VARIABLE MISSING IN CNF CONVERSION OF CONDITION")
                return
        else:
            value = evaluateTypifiedCondString(item, truthDict)

        if (value == True and type == 'OR'):
            return True
        elif (value == False and type == 'AND'):
            return False
    if type == 'AND':
        return True
    else:
        return False

def checkIfAlreadyCNF(typedCondString):
    if not typedCondString[0] == 'AND':
        return False
    else:
        for item in typedCondString[1:]:
            if isinstance(item, list):
                if not ((item[0] == 'OR') or (len(item) == 2)):
                    return False
                for subitem in item[1:]:
                    if not (isinstance(subitem, str) or (isinstance(subitem, list) and (subitem[0] in ['AND', 'NOT']) and (len(subitem) == 2))):
                        return False
    return True

def generateTruthTable(size):
    if size == 1:
        return [[True], [False]]
    else:
        thisTable = []
        oneSmaller = generateTruthTable(size-1)
        for item in oneSmaller:
            thisTable.append(item+[True])
            thisTable.append(item+[False])
        return thisTable

def conditionDictionaryFromString(conditionString, negate=False):
    splitUp = splitOnSpacesOutsideSpeechmarks(conditionString)

    if (len(splitUp) != 3):
        quitter.quitWithError("CONDITIONS MUST BE <VARIABLE NAME> <CONDITION CLASS> <COMPARISON VALUE>")
        return
    else:
        varName, persistent = persistentCheckAndStrip(splitUp[0])
        if not isValidName(varName):
            quitter.quitWithError("INVALID FORMATTING FOR VARIABLE NAME IN CONDITION")
            return
        else:
            return {"VariableToCompare": 
                    {
                        "Name": varName,
                        "Persistent": persistent
                    },
                        "ConditionClassName": splitUp[1],
                        "ComparisonValue": trimSpeechMarks(splitUp[2]),
                        "Not": negate
                    }

def generateConditionsConjunctionFromTypedString(typedCondString):
    conditionsConjunction = []
    for item in typedCondString:
        conditionsDisjunction = []
        if item[0] == 'AND' and len(item) == 2:
            conditionsDisjunction.append(conditionDictionaryFromString(item[1]))
        elif item[0] == 'NOT' and len(item) == 2:
            conditionsDisjunction.append(conditionDictionaryFromString(item[1], negate=True))
        elif item[0] == 'OR':
            for subitem in item[1:]:
                if subitem[0] == 'AND' and len(subitem) == 2:
                    conditionsDisjunction.append(conditionDictionaryFromString(subitem[1]))
                elif subitem[0] == 'NOT' and len(subitem) == 2:
                    conditionsDisjunction.append(conditionDictionaryFromString(subitem[1], negate=True))
        if len(conditionsDisjunction) > 0:
            conditionsConjunction.append({"Conditions": conditionsDisjunction})
    return conditionsConjunction

def conditionStringToCNF(conditionString):
    conditionString = conditionString.strip()
    
    simpleSplit = conditionString.split(' ')
    if len(simpleSplit) == 0 or (len(simpleSplit) > 3 and ('AND' not in simpleSplit) and ('OR' not in simpleSplit)) or (conditionString[0] in ['AND','OR']):
        quitter.quitWithError("CONDITION IS MALFORMED")

    splitCondString = splitConditionString(conditionString)

    typedCondString = typifyConditionString(splitCondString)

    if isinstance(typedCondString[1], str):
        typedCondString = ['AND', typedCondString]

    if checkIfAlreadyCNF(typedCondString):
        return generateConditionsConjunctionFromTypedString(typedCondString)

    variables = getVariablesFromConditionString(conditionString)
    truthTables = generateTruthTable(len(variables))

    falsifyingValues = []
    for j in range(0, len(truthTables)):
        truthDict = {variables[i]: truthTables[j][i] for i in range(0, len(variables))}
        if evaluateTypifiedCondString(typedCondString, truthDict) == False:
            falsifyingValues.append(truthTables[j])

    cnf = ['AND']
    for i in range(len(falsifyingValues)):
        CNFclause = ['OR']
        for j in range(len(falsifyingValues[i])):
            if falsifyingValues[i][j] == True:
                CNFclause.append(['NOT', variables[j]])
            else:            
                CNFclause.append(['AND', variables[j]])
        cnf.append(CNFclause)

    if checkIfAlreadyCNF(cnf):
        return generateConditionsConjunctionFromTypedString(cnf)
    else:
        quitter.quitWithError("FAILED TO GENERATE VALID CONJUNCTIVE NORMAL FORM OF CONDITION")
        return



#  --- PERSISTENT VARIABLES ---
def persistentCheckAndStrip(varName):
    if varName.startswith('persistent.'):
        return (varName[11:], True)
    else:
        return (varName, False)



#  --- DISPLAYABLES AND MODELS ---
def getInterpDict(viewpointAlternative=False):
    interpDict = {
        "none": "linear",
        "linear" : "Linear",
        "in" : "EaseIn",
        "easein" : "EaseIn",
        "out" : "EaseOut",
        "easeout" : "EaseOut",
        "easeinout" : "EaseInOut",
        "easeinandout" : "EaseInOut",
        "both" : "EaseInOut"}
    if viewpointAlternative: # I used a slightly different enumeration for viewpoints - I ought to fix it on the other end
        return {key:("EaseInAndOut" if value == "EaseInOut" else value) for key, value in interpDict.items()}
    else:
        return interpDict



#  --- JSON ---
def dumpJSONAndAppend(thingToDump, filePath):
    # Dumps a json representation of the given Thing to the specified file path (appending)
    with open(filePath, 'a') as outputFile:
        json.dump(thingToDump, outputFile, indent="\t")   

def appendJSON(objectWithJSONMethod, filePath):
    # ONLY for an object with its own appendJSONToFile method, runs than and appends to the specified file path (appending)
    if objectWithJSONMethod is not None:
        with open(filePath, 'a+') as JSONFile:
            if filePath.stat().st_size > 5:  #If it's too big to have just '[' in it, we need a prefixing comma
                JSONFile.write(",\n")
        objectWithJSONMethod.appendJSONToFile(filePath)



# --- PYTHON/JSON STRUCT EQUIVALENTS ---
class UnevinLineOfDialogue:
    def __init__(self):
        self.dictionary = {
            "Name": generateRandomName(),
            "ForcedDurationLineProperties": {},
            "ActiveConditionsConjunction": [],
            "Variables": [],
            "ExternalEvents": [],
            "Sprites": {
                "SpritesToShow": [],
                "SpritesToChange": [],
                "SpritesToHide": []
            },
            "Models": {
                "ModelsToShow": [],
                "ModelsToChange": [],
                "ModelsToHide": []
            },
            "Animations": {
			    "AnimationsToPlay": []
		    },
            "Viewpoint": {
                "Viewpoint": {
                    "TransitionSettings" : {}
                }
            }
        }

    def getDict(self):
        return self.dictionary
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.getDict(), outputFilePath)
        
    def setCharacter(self, characterName):
        self.dictionary["CharName"] = characterName
        
    def setBody(self, body):
        self.dictionary["Body"] = trimSpeechMarks(body)
    
    def setForcedDuration(self, duration):
        self.dictionary["ForcedDurationLineProperties"] = {
            "Enabled": True,
            "Duration": str(duration)
        }
    
    def setActiveConditions(self, conditions):
        conditionsArray = conditionStringToCNF(conditions)
        if conditionsArray is not None:
            self.dictionary["ActiveConditionsConjunction"] = conditionsArray
        else:
            quitter.quitWithError("BAD CONDITIONS")
    
    def addVariableTransform(self, varName, persistent, transformerName, modification):
        self.dictionary["Variables"].append({
            "VariableToModify":
            {
                "Name": varName,
                "Persistent": persistent
            },
            "Transformer": transformerName,
            "Modification": str(modification)
        })
    
    def addExternalEvent(self, eventName, additionalData):
        self.dictionary["ExternalEvents"].append({
				"EventName": eventName,
				"AdditionalData": str(additionalData)
			})

    def addSpriteToShow(self, spriteName, displayableID, order, tx, ty, sx, sy, duration, itx, ity, isx, isy, interp):
        orderDict = {"front": "Front", "back" : "Back"}
        self.dictionary["Sprites"]["SpritesToShow"].append({
            "SpriteName": spriteName,
            "DisplayableID": displayableID,
            "Order": orderDict.get(order.lower(), "Front"),
            "Properties": {
						"Position":
						{
							"X": str(tx),
							"Y": str(ty)
						},
						"Scale":
						{
							"X": str(sx),
							"Y": str(sy)
						}
					},
            "Transition": {
						"InitialPropertyOffsets":
						{
							"Position":
							{
								"X": str(itx),
								"Y": str(ity)
							},
							"Scale":
							{
								"X": str(isx),
								"Y": str(isy)
							}
						},
						"Interpolation": getInterpDict().get(interp.lower(), "Linear"),
						"Duration": duration
					}
        })

    def addSpriteToChange(self, spriteName, changeOrder, changePos, ntx, nty, changeSize, nsx, nsy, duration, interp):
        changeOrderDict = {"none": "DoNothing",
                           "front" : "BringToFront",
                           "bringtofront" : "BringToFront",
                           "back" : "SendToBack",
                           "sendtoback" : "SendToBack"}
        self.dictionary["Sprites"]["SpritesToChange"].append({
            "SpriteName": spriteName,
            "ChangeOrder": changeOrderDict.get(changeOrder.lower(), "DoNothing"),
            "ChangePosition": changePos,
            "ChangeSize": changeSize,
            "NewProperties": {
						"Position":
						{
							"X": str(ntx),
							"Y": str(nty)
						},
						"Scale":
						{
							"X": str(nsx),
							"Y": str(nsy)
						}
					},
            "Transition": {
						"Interpolation": getInterpDict().get(interp.lower(), "Linear"),
						"Duration": str(duration)
					}
        })

    def addSpriteToHide(self, spriteName, duration, interp, ftx, fty, fsx, fsy):
        self.dictionary["Sprites"]["SpritesToHide"].append({
            "SpriteName": spriteName,
            "Transition": {
						"FinalPropertyOffsets":
						{
							"Position":
							{
								"X": str(ftx),
								"Y": str(fty)
							},
							"Scale":
							{
								"X": str(fsx),
								"Y": str(fsy)
							}
						},
						"Interpolation": getInterpDict().get(interp.lower(), "Linear"),
						"Duration": str(duration)
					}
        })
    
    def addModelToShow(self, modelName, meshGroup, attachTag, originTag, tx, ty, tz, rx, ry, rz, sx, sy, sz, duration, interp, itx, ity, itz, irx, iry, irz, isx, isy, isz):
        tempQuat = unreal.Rotator(float(rx), float(ry), float(rz)).quaternion()
        tempTransQuat = unreal.Rotator(float(irx), float(iry), float(irz)).quaternion()
        self.dictionary["Models"]["ModelsToShow"].append({
            "ModelName": modelName,
            "MeshGroupID": meshGroup,
            "AttachTag": attachTag,
            "OriginTag": originTag,
            "Transform": {
						"Rotation":
						{
							"X": str(tempQuat.get_editor_property('x')),
							"Y": str(tempQuat.get_editor_property('y')),
							"Z": str(tempQuat.get_editor_property('z')),
							"W": str(tempQuat.get_editor_property('w'))
						},
						"Translation":
						{
							"X": str(tx),
							"Y": str(ty),
							"Z": str(tz)
						},
						"Scale3D":
						{
							"X": str(sx),
							"Y": str(sy),
							"Z": str(sz)
						}
					},
					"Transition":
					{
						"InitialTransformOffset":
						{
                            "Rotation":
                            {
                                "X": str(tempTransQuat.get_editor_property('x')),
                                "Y": str(tempTransQuat.get_editor_property('y')),
                                "Z": str(tempTransQuat.get_editor_property('z')),
                                "W": str(tempTransQuat.get_editor_property('w'))
                            },
							"Translation":
                            {
                                "X": str(itx),
                                "Y": str(ity),
                                "Z": str(itz)
                            },
                            "Scale3D":
                            {
                                "X": str(isx),
                                "Y": str(isy),
                                "Z": str(isz)
                            }
						},
						"Duration": str(duration),
						"Interpolation": getInterpDict().get(interp.lower(), "Linear")
					}
        })
    
    def addModelToChange(self, modelName, changeAttach, newAttachTag, moveToTag, duration, interp, ntx, nty, ntz, nrx, nry, nrz, nsx, nsy, nsz):
        tempQuat = unreal.Rotator(float(nrx), float(nry), float(nrz)).quaternion()
        self.dictionary["Models"]["ModelsToChange"].append({
            "ModelName": modelName,
            "ChangeAttachment": changeAttach,
            "NewAttachTag": newAttachTag,
            "MoveToTag": moveToTag,
            "TransformOffset": {
						"Rotation":
						{
							"X": str(tempQuat.get_editor_property('x')),
							"Y": str(tempQuat.get_editor_property('y')),
							"Z": str(tempQuat.get_editor_property('z')),
							"W": str(tempQuat.get_editor_property('w'))
						},
						"Translation":
						{
							"X": str(ntx),
							"Y": str(nty),
							"Z": str(ntz)
						},
						"Scale3D":
						{
							"X": str(nsx),
							"Y": str(nsy),
							"Z": str(nsz)
						}
					},
					"Transition":
					{
						"Duration": str(duration),
						"Interpolation": getInterpDict().get(interp.lower(), "Linear")
					}
        })
    
    def addModelToHide(self, modelName, duration, interp, ftx, fty, ftz, frx, fry, frz, fsx, fsy, fsz):
        tempQuat = unreal.Rotator(float(frx), float(fry), float(frz)).quaternion()
        self.dictionary["Models"]["ModelsToHide"].append({
            "ModelName": modelName,
            "Transition":
            {
                "FinalTransformOffset":
                {
                    "Rotation":
                    {
                        "X": str(tempQuat.get_editor_property('x')),
                        "Y": str(tempQuat.get_editor_property('y')),
                        "Z": str(tempQuat.get_editor_property('z')),
                        "W": str(tempQuat.get_editor_property('w'))
                    },
                    "Translation":
                    {
                        "X": str(ftx),
                        "Y": str(fty),
                        "Z": str(ftz)
                    },
                    "Scale3D":
                    {
                        "X": str(fsx),
                        "Y": str(fsy),
                        "Z": str(fsz)
                    }
                },
                "Duration": str(duration),
                "Interpolation": getInterpDict().get(interp.lower(), "Linear")
            }
        })
        
    def addAnimation(self, modelName, animName, loop):
        self.dictionary["Animations"]["AnimationsToPlay"].append({
            "Model": modelName,
            "Animation": animName,
            "Loop": loop
        })
        
    def addDialogueBoxAnimation(self, direction, duration, animation):
        directionDict = {"show" : "Show", "hide" : "Hide"}
        animDict = {"slide" : "Slide", "fade" : "Fade"}
        self.dictionary["DialogBox"] = {
            "Enabled": True,
			"Direction": directionDict.get(direction.lower(), "Hide"),
			"Duration": str(duration),
			"Animation": animDict.get(animation.lower(), "Fade")
        }
    
    def enableViewportChange(self):
        self.dictionary["Viewpoint"]["ViewpointChangeEnabled"] = True
    
    def setLevelChange(self, newlevelname):
        self.enableViewportChange()
        self.dictionary["Viewpoint"]["Viewpoint"]["LevelName"] = newlevelname
    
    def setViewpointChange(self, newcamtag):
        self.enableViewportChange()        
        self.dictionary["Viewpoint"]["Viewpoint"]["CameraTagName"] = newcamtag
    
    def setViewpointTransitionType(self, blendType):
        blendType = getInterpDict(viewpointAlternative=True).get(blendType.lower(), "Linear")
        self.dictionary["Viewpoint"]["Viewpoint"]["TransitionSettings"]["BlendType"] = blendType
    
    def setViewpointTransitionBlendTime(self, blendTime):
        self.dictionary["Viewpoint"]["Viewpoint"]["TransitionSettings"]["BlendTime"] = str(blendTime)
    
    def setViewpointTransitionBlendExponent(self, blendExponent):
        self.dictionary["Viewpoint"]["Viewpoint"]["TransitionSettings"]["BlendExponent"] = str(blendExponent)

    def setChoiceGroup(self, choiceGroupAssetPath):
        self.dictionary["Choices"] = {
			"ChoicesEnabled": True,
			"ChoiceGroup": choiceGroupAssetPath
		}

    def setDestination(self, sceneDTAssetPath, isCall):
        self.dictionary["Destination"] = {
            "Enabled": True,
            "Destination":
            {
                "Scene": sceneDTAssetPath,
                "RowName": "None"
            },
            "IsCall": isCall
        }

    def setPlayerInput(self, varName, persistent, default="", showDefault=False, processors=[]):
        self.dictionary["PlayerInput"] = {
            "InputPromptEnabled": True,
			"VariableToSet":
			{
				"Name": varName,
				"Persistent": persistent
			},
			"StringProcessors": processors,
			"DefaultValue": trimSpeechMarks(str(default)),
			"ShowDefault": showDefault
        }

    def setDestination(self, sceneDTAssetPath, isCall):
        self.dictionary["Destination"] = {
            "Enabled": True,
            "Destination":
            {
                "Scene": sceneDTAssetPath,
                "RowName": "None"
            },
            "IsCall": isCall
        }


        



class UnevinChoice:
    def __init__(self):
        self.dictionary = {
            "Name": generateRandomName()
        }

    def getDict(self):
        return self.dictionary
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.getDict(), outputFilePath)
        
    def setName(self, name):
        self.dictionary["Name"] = trimSpeechMarks(name)
        
    def setBody(self, body):
        self.dictionary["Body"] = trimSpeechMarks(body)
    
    def setDestination(self, sceneDTpath, isCall):
        self.dictionary["Destination"] = {
            "Enabled": True,
            "Destination":
            {
                "Scene": sceneDTpath,
                "RowName": "None"
            },
            "IsCall": isCall
        }
    
    def setVisibleConditions(self, conditions):
        conditionsArray = conditionStringToCNF(conditions)
        if conditionsArray is not None:
            self.dictionary["VisibleConditionsConjuction"] = conditionsArray
        else:
            quitter.quitWithError("BAD VISIBILITY CONDITIONS FOR CHOICE")
    
    def setActiveConditions(self, conditions):
        conditionsArray = conditionStringToCNF(conditions)
        if conditionsArray is not None:
            self.dictionary["ActiveConditionsConjuction"] = conditionsArray
        else:
            quitter.quitWithError("BAD ACTIVATION CONDITIONS FOR CHOICE")
    
    def setOverrideColours(self, tr, tg, tb, ta, br, bg, bb, ba):
        self.dictionary["OverrideColours"] = {
			"EnableColourOverrides": True,
			"TextColour":
			{
				"R": str(tr),
				"G": str(tg),
				"B": str(tb),
				"A": str(ta)
			},
			"ButtonColour":
			{
				"R": str(br),
				"G": str(bg),
				"B": str(bb),
				"A": str(ba)
			}
		}

class Character:
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

    def getDict(self):
        return self.dictionary
        
    def appendJSONToFile(self, outputFilePath):
        dumpJSONAndAppend(self.getDict(), outputFilePath)
    
    def setName(self, name):
        self.dictionary["Name"] = name
    
    def setDisplayName(self, dname):
        self.dictionary["DisplayName"] = dname
    
    def setColor(self, color):
        color = color.replace("#","")
        self.dictionary["Color"] = {"R": str(int(color[:2], 16)), "G": str(int(color[2:4], 16)), "B": str(int(color[4:6], 16)), "A": 255}