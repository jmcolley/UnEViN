import unreal
import sys
import re
import renpyhax as renpy
from pprint import pprint

def getPrettierRenpyASTObjectPrintRepresentation(node):
    finalPrintString = str(node)
    
    if isinstance(node, renpy.ast.Define) or isinstance(node, renpy.ast.Default):
        finalPrintString += ("  ----  Variable: " + str(node.varname) + "  ----  Value: " + str(node.code.source))
    elif isinstance(node, renpy.ast.Say):
        finalPrintString += ("  ----  Who: " + str(node.who) + "  ----  What: " + str(node.what) + "  ----  Attributes: " + str(node.attributes))
    elif isinstance(node, renpy.ast.Scene):
        finalPrintString += ("  ----  ImSpec: " + str(node.imspec) + "  ----  Layer: " + str(node.layer) + "  ----  ATL: " + str(node.atl))
    elif isinstance(node, renpy.ast.With):
        finalPrintString += ("  ----  Expression: " + str(node.expr) + "  ----  Paired: " + str(node.paired))
    elif isinstance(node, renpy.ast.Show):
        finalPrintString += ("  ----  ImSpec: " + str(node.imspec) + "  ----  ATL: " + str(node.atl))
    elif isinstance(node, renpy.ast.Jump):
        finalPrintString += ("  ----  Target: " + str(node.target) + "  ----  Expression: " + str(node.expression) + "  ----  GlobalLabel: " + str(node.global_label))
    elif isinstance(node, renpy.ast.Label):
        finalPrintString += ("  ----  Name: " + str(node.name) + "  ----  Parameters: " + str(node.parameters))
    elif isinstance(node, renpy.ast.Return):
        finalPrintString += ("  ----  Expression: " + str(node.expression))
    elif isinstance(node, renpy.ast.Python):
        finalPrintString += ("  ----  Code: " + str(node.code))
    elif isinstance(node, renpy.ast.Menu):
        finalPrintString += ("  ----  Items: " + str(node.items) + "  ----  Set: " + str(node.set) + "  ----  HasCaption: " + str(node.has_caption) + "  ----  With: " + str(node.with_) + "  ----  Arguments: " + str(node.arguments) + "  ----  ItemArguments: " + str(node.item_arguments))
        
    return finalPrintString


def recursiveRenpyASTPrint(node, depth):
    print(("    "*depth)+getPrettierRenpyASTObjectPrintRepresentation(node))    
    if isinstance(node, renpy.ast.Init) or isinstance(node, renpy.ast.Label):
        for child in node.block:
            recursiveRenpyASTPrint(child, depth+1)

def isProbablyBoolNumberOrString(potentialval):
    if varval.lower() == "true" or varval.lower() == "false":
        return True
    elif varval.isdigit():
        return True
    elif potentialval.startswith('"') and potentialval.endswith('"') and not potentialval.endswith('\\"'):
        return True
    elif potentialval.startswith("'") and potentialval.endswith("'") and not potentialval.endswith("\\'"):
        return True
    else:
        return False

rpyFileName = sys.argv[1]
rpyFilePath = "../../../../Projects/UnEViN/Content/"+rpyFileName+".rpy"
rpyUEBasePath = "/Game/"+rpyFileName

for node in renpy.parser.parse(rpyFilePath):
    recursiveRenpyASTPrint(node, 0)
    
unreal.EditorAssetLibrary.make_directory(rpyUEBasePath)
unreal.EditorAssetLibrary.make_directory(rpyUEBasePath+"/Scenes")
unreal.EditorAssetLibrary.make_directory(rpyUEBasePath+"/ChoiceGroups")
newCharactersTable = unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Characters_Empty", rpyUEBasePath+"/DT_Characters_"+rpyFileName)
initSceneTable = unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Scene_Empty", rpyUEBasePath+"/DT_Scene_Init_"+rpyFileName)

charactersCSVLine = '---,DisplayName,Color'
baseSceneCSVLine = '---,Type,CharName,Body,Destination,DestinationJumpIsCall,Conditions,VariablesToSet,ChoiceGroup,InputPrompt'
baseChoicesCSVLine = '---,Body,Destination,DestinationJumpIsCall,VisibleConditions,ActiveConditions'
initSceneCSVLine = baseSceneCSVLine
pendingDataTableFills = []

i=0
for node in renpy.parser.parse(rpyFilePath):
    i+=1
    if isinstance(node, renpy.ast.Init):        
        for child in node.block:
            i+=1
            if isinstance(child, renpy.ast.Define) or isinstance(child, renpy.ast.Default):
                varname = child.varname
                varval = child.code.source
                if varval.startswith("Character("):
                    charName = "Default Name"
                    charColor = "ffffff"
                    
                    characterDefinition = varval[10:-1].split(",")
                    
                    charNameMatch = re.compile('\".*?\"').search(characterDefinition[0])
                    if charNameMatch is not None:
                        charName = charNameMatch.group(0)[1:-1]
                    
                    for argument in characterDefinition[1:]:
                        argument = argument.strip()
                        if argument.startswith("color=") or argument.startswith("who_color="):                    
                            charColorMatch = re.compile('\"\#......\"').search(argument)
                            if charColorMatch is not None:
                                charColor = charColorMatch.group(0)[2:-1]
                    
                    r, g, b = str(int(charColor[:2], 16)), str(int(charColor[2:4], 16)), str(int(charColor[4:6], 16))
                    charactersCSVLine += f'\n{varname},"{charName}","(B={b},G={g},R={r},A=255)"'
                else:
                    if isProbablyBoolNumberOrString(varval):
                        varval = varval.strip('"\'')
                    else:
                        varval = f'[{varval}]'
                    initSceneCSVLine += f'\n{i},"InstantAdvance",,,"()",,,"((Name=""{varname}"",Value=""{varval}"",Persistent=False))",,"()"'                    
    elif isinstance(node, renpy.ast.Label):        
        unreal.EditorAssetLibrary.make_directory(rpyUEBasePath+"/Scenes/"+str(node.name))
        labelSceneTable = unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Scene_Empty", rpyUEBasePath+"/Scenes/"+str(node.name)+"/DT_Scene_"+str(node.name)+"_Main")     
        labelSceneCSVLine = baseSceneCSVLine
        for child in node.block:
            i+=1
            menuCount=0
            if isinstance(child, renpy.ast.Say):
                char = child.who
                saidline = child.what
                if not char in ["play"]:
                    labelSceneCSVLine += f'\n{i},"Normal","{char}","{saidline}","()",,,"()",,"()"'
            elif isinstance(child, renpy.ast.Jump):
                jumpPath = rpyUEBasePath+"/Scenes/"+str(child.target)+"/DT_Scene_"+str(child.target)+"_Main."+"DT_Scene_"+str(child.target)+"_Main"
                labelSceneCSVLine += f'\n{i},"InstantAdvance","","","(Scene=""/Script/Engine.DataTable\'{jumpPath}\'"",RowName="""")",,,"()",,"()"'
            elif isinstance(child, renpy.ast.Menu):
                menuCount+=1
                choicesTableDir = rpyUEBasePath+"/ChoiceGroups/"+str(node.name)
                choicesTableFilename = "DT_ChoiceGroup_"+str(node.name)+"_"+str(menuCount)
                menuChoicesTable = unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Choices_Empty", choicesTableDir+"/"+choicesTableFilename)
                menuChoicesCSVLine = baseChoicesCSVLine
                menuitems = child.items
                if menuitems[0][2] is None:
                    labelSceneCSVLine += f'\n{i},"Normal","","{menuitems[0][0]}","()",,,"()",,"()"'
                    menuitems = menuitems[1:]
                for item in menuitems:
                    i+=1
                    destination = "()"
                    itemConsequences = item[2]
                    if len(itemConsequences)==1 and isinstance(itemConsequences[0], renpy.ast.Jump):
                        target = str(itemConsequences[0].target)
                        jumpPath = rpyUEBasePath+"/Scenes/"+target+"/DT_Scene_"+target+"_Main."+"DT_Scene_"+target+"_Main"
                        destination = f'(Scene=""/Script/Engine.DataTable\'{jumpPath}\'"",RowName="""")'
                    menuChoicesCSVLine += f'\n{i},"{item[0]}","{destination}","","",""'
                pendingDataTableFills.append((menuChoicesTable, menuChoicesCSVLine))
                if child.has_caption:
                    disassembled = labelSceneCSVLine.split('\n')
                    disassembled[-1] = (disassembled[-1][:-5]+f'"/Script/Engine.DataTable\'{choicesTableDir}/{choicesTableFilename}.{choicesTableFilename}\'"'+',"()"').replace("Normal", "Choice")
                    labelSceneCSVLine = "\n".join(disassembled)
                else:
                    labelSceneCSVLine += f'\n{i},"Choice","","","()",,,"()","/Script/Engine.DataTable\'{choicesTableDir}/{choicesTableFilename}.{choicesTableFilename}\'","()"'
        pendingDataTableFills.append((labelSceneTable, labelSceneCSVLine))
        
unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(newCharactersTable, charactersCSVLine)
characterCompTable = unreal.EditorAssetLibrary.load_asset("/Game/UnEViN/Core/DT_Comp_Characters")
characterTables = characterCompTable.get_editor_property("ParentTables")
if not newCharactersTable in characterTables:
    characterTables.insert(0, newCharactersTable)
characterCompTable.set_editor_property("ParentTables", characterTables, notify_mode = unreal.PropertyAccessChangeNotifyMode.ALWAYS)
characterCompTable.modify()

for fill in pendingDataTableFills:
    unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(fill[0], fill[1])
      
startPath = rpyUEBasePath+"/Scenes/start/DT_Scene_start_Main."+"DT_Scene_start_Main"
initSceneCSVLine += f'\nbeginGame,"InstantAdvance","","","(Scene=""/Script/Engine.DataTable\'{startPath}\'"",RowName="""")",,,"()",,"()"'
unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(initSceneTable, initSceneCSVLine)

initPath = rpyUEBasePath+f'/DT_Scene_Init_{rpyFileName}.DT_Scene_Init_{rpyFileName}'
startSceneCSVLine = baseSceneCSVLine + f'\nbeginGame,"InstantAdvance","","","(Scene=""/Script/Engine.DataTable\'{initPath}\'"",RowName="""")",,,"()",,"()"'
startTable = unreal.EditorAssetLibrary.load_asset("/Game/UnEViN/Core/DT_Start")
unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(startTable, startSceneCSVLine)