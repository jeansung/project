#imports
from rule_parser import *
import codecs
import sys
from reference_dictionaries import *
from process_rules import *
from xlrd import open_workbook
from xlwt import *
from xlutils.copy import copy

# File that takes the rule and table info file to generate the constraints
# and add to the Sandbox file so that it is a usable environment. 

TRUE_MESSAGE = "okay"
FALSE_MESSSAGE = "bad"
EXCEL_FILE_EXTENSION = ".xls"

# Global
tableExcelfName = ""
freeRow = 0
freeCol = 0
numInputsCol = 0
intermediateSumRow = 0
typeRowMapping = {}
valueColMapping = {}
valueColMappingReverse = {}

def main():

	# Reading in the rules
	(rulefName, supportingfName) = properInputFiles()
	ruleStrings = readRulesFromInputFile(rulefName)

	# Check the Syntax Errors and References to non existence rules	
	# Parse Rules
	rules = parseRules(ruleStrings)

	# Read in supporting file / initialize globals
	readInExcelInfo(supportingfName)

	# Creating the Excel Formulas
	nameFormulaPairs = generateExcelFormulas(rules)

	# open previous excel worksheet 
	# rb = open_workbook(tableExcelfName + EXCEL_FILE_EXTENSION,formatting_info=True)
	# wb = copy(rb)
	# ws = wb.sheet_by_index(0)

	# ## find space to write it
	# nameCol = 0
	# formulaCol = 1
	# startRow = freeRow + 2
	# numRules = len(rules)

	# for row in range(numRules):
	# 	adjustedRow = startRow + row
	# 	currName = nameFormulaPairs[row][0]
	# 	currFormula = nameFormulaPairs[row][1]
	# 	ws.write(row, nameCol, currName)
	# 	ws.write(row, formulaCol, currFormula)


	# wb.save(tableExcelfName + EXCEL_FILE_EXTENSION)
	
	return nameFormulaPairs
	  

	# Write Rules 

def readInExcelInfo(supportingfName):
	try:
		f = codecs.open(supportingfName)
	except IOError:
		print "Types file incorrectly formatting or does not exist."
		sys.exit(0)

	try:
		# First 2 lines are garbage
		f.readline()
		f.readline()

		global tableExcelfName 
		global freeRow
		global freeCol
		global numInputsCol
		global intermediateSumRow
		global typeRowMapping 
		global valueColMapping 
		global valueColMappingReverse

		tableExcelfName = f.readline().rstrip()
		freeRow = eval(f.readline().rstrip())
		freeCol = eval(f.readline().rstrip())
		numInputsCol =  eval(f.readline().rstrip())
		intermediateSumRow = eval(f.readline().rstrip())
		typeRowMapping = eval(f.readline().rstrip())
		valueColMapping = eval(f.readline().rstrip())
		valueColMappingReverse = eval(f.readline().rstrip())

	except SyntaxError or NameError:
		print "Incorrectly formatted supporting file."
		sys.exit(0)

	return 

# Returns a list of tuples (name, formula string) for a list of 
# parsed rules. Using the TYPE_INDEX position to determine which
# rule type (and thus which function) to use in creating Excel
# formula. 
def generateExcelFormulas(parsedRules):
	nameFormula = []
	for r in parsedRules:
		ruleType = r.rule_type.typing 
		if (ruleType == RuleType('valueRule')):
			(name, formula) = createValueRule(r)
			nameFormula.append((name, formula))
		elif (ruleType == RuleType('typeRule')):
			(name, formula) = createTypeRule(r)
			nameFormula.append((name, formula))
		else:
			print "Error. Non supported rule type."
			sys.exit(0)
	return nameFormula

# Creating a typeRule
# Input: Parsed Type Rule
# Output: (Name, Excel formula string)
def createTypeRule(r):
	logicalTest = ""
	operatorStr = OPERATOR_MAPPING[r.rule_type.operator]
	valueStr = str(r.rule_type.value)
	inputColLetter =  EXCEL_ROW_MAPPING[numInputsCol]

	# Parsing Types  => Excel 
	types = r.rule_type.type_list
	sumElements = []
	for t in types:
		row = typeRowMapping[t]
		element = str(inputColLetter) + str(row)
		sumElements.append(element)

	if (r.rule_type.relation == Relation("together")):
		# Creating Sum String 
		innerSum = "+".join(sumElements)
		logicalTest = "SUM(" + innerSum + ")" + operatorStr + valueStr 
	elif (r.rule_type.relation == Relation("each")):
		individualCheck = []
		for e in sumElements:
			currentCheck = "(" + str(e) + operatorStr + valueStr + ")"
			individualCheck.append(currentCheck)
		logicalTest = "*".join(individualCheck)
	else:
		print "Error on the relation"
		sys.exit(0)

	formulaStr = "IF(" + logicalTest + "," + TRUE_MESSAGE + "," + \
		FALSE_MESSSAGE + ")"

	return (r.name, formulaStr)

# Creating a valueRule
# Input: Parsed Value Rule
# Output: (Name, Excel formula string)
def createValueRule(r):
	logicalTest = ""
	operatorStr = OPERATOR_MAPPING[r.rule_type.operator]
	valueStr = str(r.rule_type.value)
	types = r.rule_type.type_list

	if (r.rule_type.relation == Relation("together")):
		allSumElements = []
		for t in types:
			sumElements = []
			for vLocation in valueColMappingReverse:
				elementColLetter = EXCEL_ROW_MAPPING[vLocation]
				elementRow = typeRowMapping[t]
				element = elementColLetter + str(elementRow)
				weight = str(valueColMappingReverse[vLocation])
				innerSum = "(" + element + "*" + weight + ")"
				sumElements.append(innerSum)
			perTypeWeightedSum = "(" + "+".join(sumElements) + ")"
			allSumElements.append(perTypeWeightedSum)
		totalSumString = "(" + "+".join(allSumElements) + ")"
		logicalTest = "SUM(" + totalSumString + ")" + operatorStr + valueStr 
	elif (r.rule_type.relation == Relation("each")):
		individualCheck = []
		for t in types:
			sumElements = []
			for vLocation in valueColMappingReverse:
				elementColLetter = EXCEL_ROW_MAPPING[vLocation]
				elementRow = typeRowMapping[t]
				element = elementColLetter + str(elementRow)
				weight = str(valueColMappingReverse[vLocation])
				innerSum = "(" + element + "*" + weight + ")"
				sumElements.append(innerSum)
			perTypeWeightedSum = "(" + "+".join(sumElements) + ")"
			currentCheck = "(" + perTypeWeightedSum + operatorStr + \
				valueStr + ")"
			individualCheck.append(currentCheck)
		logicalTest = "*".join(individualCheck)
	else:
		print "Error on the relation"
		sys.exit(0)

	formulaStr = "IF(" + logicalTest + "," + TRUE_MESSAGE + "," + \
		FALSE_MESSSAGE + ")"
	
	return (r.name, formulaStr)

	# Parsing Types  => Excel 
	
	sumElements = []
	for t in types:
		row = typeRowMapping[t]
		element = str(inputColLetter) + str(row)
		sumElements.append(element)

	if (r.rule_type.relation == Relation("together")):

		# Creating Sum String 
		innerSum = "+".join(sumElements)
		logicalTest = "SUM(" + innerSum + ")" + operatorStr + valueStr 
	elif (r.rule_type.relation == Relation("each")):
		individualCheck = []
		for e in sumElements:
			currentCheck = "(" + str(e) + operatorStr + valueStr + ")"
			individualCheck.append(currentCheck)
		logicalTest = "*".join(individualCheck)
	else:
		print "Error on the relation"
		sys.exit(0)

	formulaStr = "IF(" + logicalTest + "," + TRUE_MESSAGE + "," + \
		FALSE_MESSSAGE + ")"

	return (r.name, formulaStr)


# automatically runs main
if __name__ == '__main__':
	main()
