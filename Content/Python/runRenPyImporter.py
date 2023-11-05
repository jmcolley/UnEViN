import renpyhax as renpy
from pprint import pprint

def getPrettierRenpyASTObjectPrintRepresentation(node):
    finalPrintString = str(node)
    
    if isinstance(node, renpy.ast.Define) or isinstance(node, renpy.ast.Default):
        finalPrintString += ("  ----  Variable: " + str(node.varname) + "  ----  Value: " + str(node.code.source))
    elif isinstance(node, renpy.ast.Say):
        finalPrintString += ("  ----  Who: " + str(node.who) + "  ----  What: " + str(node.what))
    elif isinstance(node, renpy.ast.Scene):
        finalPrintString += ("  ----  ImSpec: " + str(node.imspec) + "  ----  Layer: " + str(node.layer) + "  ----  ATL: " + str(node.atl))
    elif isinstance(node, renpy.ast.With):
        finalPrintString += ("  ----  Expression: " + str(node.expr) + "  ----  Paired: " + str(node.paired))
    elif isinstance(node, renpy.ast.Show):
        finalPrintString += ("  ----  ImSpec: " + str(node.imspec) + "  ----  ATL: " + str(node.atl))
    elif isinstance(node, renpy.ast.Jump):
        finalPrintString += ("  ----  Target: " + str(node.target) + "  ----  Expression: " + str(node.expression) + "  ----  GlobalLabel: " + str(node.global_label))
    elif isinstance(node, renpy.ast.Label):
        finalPrintString += ("  ----  Parameters: " + str(node.parameters))
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

for renpyast in renpy.parser.parse("../../../../Projects/UnEViN/Content/Python/thequestion.rpy"):
    recursiveRenpyASTPrint(renpyast, 0)