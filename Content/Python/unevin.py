import json

def outputSceneJSON(arrayOfLinesOfDialog, outputFilePath):
    print(arrayOfLinesOfDialog)
    with open(outputFilePath, 'w') as testfile:
        json.dump([lod.getDict() for lod in arrayOfLinesOfDialog], testfile, indent="\t")

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
        
    def getDict(self):
        return self.dictionary