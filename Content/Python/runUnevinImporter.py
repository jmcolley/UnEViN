import unreal, unevin, sys
from pathlib import Path


unevinScriptFilePath = Path(sys.argv[1])
unevinScriptFolder = unevinScriptFilePath.parent
unevinScriptName = unevinScriptFilePath.stem

UNEVINTestTable = unreal.EditorAssetLibrary.duplicate_asset("/Game/UnEViN/Core/BlankDTs/DT_Scene_Empty", f"/Game/{unevinScriptName}/Scenes/DT_Scene_Test")



tempJSONFilePath = unevinScriptFolder/f"{unevinScriptName}_temp.json"

testLine = unevin.LineOfDialog()
unevin.outputSceneJSON([testLine], tempJSONFilePath)

unreal.DataTableFunctionLibrary.fill_data_table_from_json_file(UNEVINTestTable, str(tempJSONFilePath))