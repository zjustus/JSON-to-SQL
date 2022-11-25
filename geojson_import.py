import json, sys, copy, re, inquirer


class SQL_col:
    def __init__(self, name:str, Type:type, primary:bool = False, foreignTable:str = None):
        self.name = name
        self.Type = Type
        self.primary = primary

        if foreignTable is None: self.foreign = False
        else: self.foreign = True

        self.foreignTable = foreignTable

    def __str__(self):
        keyType = "Not a Key"
        if self.primary: keyType = "Primary"
        elif self.foreign: keyType = "Foreign Table "+ self.foreignTable
        return f'Name: {self.name} | {self.Type} | {keyType}'


# A helper function that checks if a dictionary contains a dictionary
def dict_contains_dict(f_input:dict):
    for x in f_input:
        if(type(f_input[x]) is dict): 
            return True
    return False

# A helper function that checks if every object in a list has the same structure
def list_struct_check(f_input:list):
    base = type(f_input[0])
    for i in f_input:
        if type(i) is not base: return False
    
    if(base is dict):
        base_keys = f_input[0].keys()
        for i in f_input:
            if i.keys() != base_keys: return False
    
    return True

# A function that converts all nested dicts into its top level. 
def python_dict_flatten(f_input:dict):
    output = copy.deepcopy(f_input)

    while(dict_contains_dict(f_input)):
        for key in f_input:
            if(type(f_input[key]) is dict):
                some_dict = output.pop(key)
                for some_key in some_dict:
                    output[key + "_" + some_key] = some_dict[some_key]
            elif(type(f_input[key]) is list and type(f_input[key][0]) is dict):
                for i in range(len(output[key])):
                    output[key][i] = python_dict_flatten(output[key][i])

        
        f_input = output
    return output

# A function that converts all lists of lists into lists of dicts
# TODO: add catch for lists of regular data
def python_dict_list_list_convert(f_input:dict):
    for key in f_input:
        if type(f_input[key]) is list:
            if type(f_input[key][0]) is dict:
                for i in range(len(f_input[key])):
                    f_input[key][i] = python_dict_list_list_convert(f_input[key][i])
            if type(f_input[key][0]) is list:
                # new_col = []
                for i in range(len(f_input[key])):
                    new_row = dict()
                    for j in range(len(f_input[key][i])):
                        new_row[key + "_" +str(j)] = f_input[key][i][j]
                    # new_col.append(new_row)
                    f_input[key][i] = new_row
                # f_input[key] = new_row
    return f_input

# HOLD: A function that appends primary keys to all rows

# HOLD: A function that appends foreign keys to all rows

# HOLD: A function that allows the renaming of column names

# HOLD: A function that inserts data into a table

# A function that takes a processed JSON dictionary and returns an object denoted with its structure
def create_sql_dict_from_json(f_input:dict, tableName:str = "main", foreign_key:SQL_col = None, sql_dict:dict = dict()):
    sql_dict[tableName + "_struct"] = []
    # TODO: Prompt for primary key, if none is chosen, create one
    
    primary = SQL_col(tableName+"_pk", int, True)
    sql_dict[tableName + "_struct"].append(primary)
    if foreign_key is not None: sql_dict[tableName + "_struct"].append(foreign_key)

    child_foreign_key = SQL_col(primary.name, primary.Type, False, tableName)

    for key in f_input:
        if type(f_input[key]) is list:
            if type(f_input[key][0]) is dict:
                sql_dict = create_sql_dict_from_json(f_input[key][0], key, child_foreign_key, sql_dict)
            else:
                print("Error, all lists must be converted into dictionaries, ignoring this column, sorry, no further debug information :P")
        else:
            sql_dict[tableName + "_struct"].append(SQL_col(key, type(f_input[key])))
    return sql_dict


# A function that prints the keys of every dict in a NOT processed JSON dictionary
def print_dict_as_tables(f_input:dict, tableName:str = "main"):

    # Print table Structure
    print(tableName, "Table")
    print("--------------")
    for key in f_input:
        print(key, " : ", type(f_input[key]))
    print()

    for key in f_input:
        if type(f_input[key]) is list:
            if not list_struct_check(f_input[key]):
                print("Error, List is not uniform")
                return False
            if type(f_input[key][0]) is dict:
                print_dict_as_tables(f_input[key][0], tableName + " > " + key)
    return True

def print_sql_struct(f_input:dict):
    tables = [val for val in f_input.keys() if "_struct" in val]
    for table in tables:
        print(table, "Table")
        print("----------------")
        for col in f_input[table]:
            print(col)
        print()
        print()


def create_sql_struct_from_dict(f_input:dict, sqlFile, tableName:str = "main", foreignKey = None):
    
    # Create the SQL Line
    sqlFile.write("CREATE TABLE " + tableName + "(")
    i = 0
    for key in f_input:
        i += 1
        isWritten = False
        if(type(f_input[key]) is int):
            sqlFile.write(key+" int")
            isWritten = True
        if(type(f_input[key]) is float):
            sqlFile.write(key+" float")
            isWritten = True
        elif(type(f_input[key]) is str):
            sqlFile.write(key+" text")
            isWritten = True
        if(i != len(f_input) and isWritten == True): sqlFile.write(", ")
    sqlFile.write(");\n")

    # Go to Next Table
    for column in f_input:
        if type(f_input[column]) is list:
            if type(f_input[column][0]) is dict:
                create_sql_struct_from_dict(f_input[column][0], sqlFile, column)



# Start of pragmatic flow

# Get Json File
json_file_name = ""
if(len(sys.argv) > 1):
    json_file_name = sys.argv[1]
else:
    json_file_name = input("path and Name of JSON file: ")

# Parse Json file into python dict
print("Parsing File")
json_file = open(json_file_name, "r")
json_content = json.loads(json_file.read())
json_file.close()

# Condition and Print structure
print("Flattening JSON")
json_content = python_dict_flatten(json_content)
print("Creating SQL structure")
json_content = python_dict_list_list_convert(json_content)
print()
print("Printing Structure")
# print_dict_as_tables(json_content, "Geometry")
print()
print()

sql_dict = create_sql_dict_from_json(json_content, "main")
print_sql_struct(sql_dict)



# print("Creating Output")
# sql_out = open("output.sql", "w")
# create_sql_struct_from_dict(json_content, sql_out, "Geometry")
# sql_out.close()
# print("Output created")




