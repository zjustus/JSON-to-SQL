import json, sys, copy, re, inquirer

# This Object helps define the struct of a SQL table
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
        elif self.foreign: keyType = "Foreign, Table "+ self.foreignTable
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

# A function that should standardize content
# TODO: STANDARDIZE IT!!!
def python_json_standardize(f_input:dict, sample=None):
    if sample is not None:
        if type(sample) is dict:
            print("TODO: Sample is dict")
        else:
            print("TODO: sample is other")

    for key in f_input:
        if type(f_input[key]) is list:
            for i in range(len(f_input[key])):
                print("TODO!")
                # check if the structure of index 0 matches the structure of the rest
        elif type(f_input[key] is dict):
            for i in f_input[key]:
                python_json_standardize(f_input[key][i], f_input[key][0])
                
                

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

# A function that takes a processed JSON dictionary and returns an object denoted with its structure
def create_sql_dict_from_json(f_input:dict, tableName:str = "main", foreign_key:SQL_col = None, sql_dict:dict = dict()):
    sql_dict[tableName + "_struct"] = []

    # This section defines primary and child foreign keys
    primaryKeyChoice = ["~None~"]
    for key in f_input:
        if type(f_input[key]) is not list:
            primaryKeyChoice.append(key)
    questions = [
        inquirer.List(
            "pk",
            message="What is the primary key for the "+tableName+" table?",
            choices=primaryKeyChoice
        )
    ]
    primaryKeyChosen = inquirer.prompt(questions)

    if primaryKeyChosen["pk"] != "~None~":
        pkName = primaryKeyChosen["pk"]
        pkType = type(f_input[pkName])
        child_foreign_key = SQL_col(pkName, pkType, False, tableName)
    else: 
        sql_dict[tableName + "_struct"].append(SQL_col(tableName+'_pk', int, True))
        child_foreign_key = SQL_col(tableName+'_pk', int, False, tableName)

    # This section creates table structure based on first dict in every list
    if foreign_key is not None: sql_dict[tableName + "_struct"].append(foreign_key)
    for key in f_input:
        if type(f_input[key]) is list:
            if type(f_input[key][0]) is dict:
                sql_dict = create_sql_dict_from_json(f_input[key][0], key, child_foreign_key, sql_dict)
            else:
                print("Error, all lists must be converted into dictionaries, ignoring this column, sorry, no further debug information :P")
        else:
            sql_dict[tableName + "_struct"].append(SQL_col(
                key, 
                type(f_input[key]), 
                True if key == primaryKeyChosen["pk"] else False
            ))

    return sql_dict

# This Function created SQL dict data given SQL structure and processed JSON input
# TODO: This Function is broken?
def create_sql_data_from_json(f_input:dict, sql_dict:dict, tableName:str = "main", foreign_key:str = None, foreign_value=None):
    
    # Load the structure
    if tableName+"_struct" not in sql_dict:
        print("Error, table structure not found, Skipping Row")
        print(tableName+"_struct")
        print(f_input)
        print()
        return sql_dict
    tableStruct = sql_dict[tableName+"_struct"]

    # Create data sector if not exists
    if tableName not in sql_dict: sql_dict[tableName] = []
    
    # Identify primary key/Value
    primaryKey = None
    primaryValue = None
    for col in tableStruct:
        if col.primary: primaryKey = col.name
        
    if primaryKey in f_input.keys():
        primaryValue = f_input[primaryKey]

    # Create new data insert and append foreign key values
    newEntry = {}
    if foreign_key is not None:
        newEntry[foreign_key] = foreign_value

    # Insert the data into the row. passing down primary key when recursive
    for key in f_input:
        if type(f_input[key]) is list:
            if type(f_input[key][0] is dict):
                for x in f_input[key]:
                    sql_dict = create_sql_data_from_json(x, sql_dict, key, primaryKey, primaryValue)
            else: print("ERROR all lists of lists must be converted to lists of dicts")
        else:
            newEntry[key] = f_input[key]

    sql_dict[tableName].append(newEntry)
    return sql_dict


# TODO: Extend this to also create the data
def create_mysql_struct_from_dict(sql_dict:dict, sql_file):

    # Part 1, create tables
    tables = [val for val in sql_dict.keys() if "_struct" in val]
    for table in tables:
        table_name = table.replace("_struct","")
        sql_file.write("CREATE TABLE "+table_name+"(")
        print("Creating table", table_name)
        i = 0
        for col in sql_dict[table]:
            i += 1
            sql_file.write(col.name+" ")

            if(col.Type is str): sql_file.write("TEXT")
            elif(col.Type is int or bool): sql_file.write("FLOAT")
            else: sql_file.write("UNKNOWN")

            if(col.primary): sql_file.write(" PRIMARY KEY")
            if(col.foreign): sql_file.write(" FOREIGN KEY REFERENCES "+col.foreignTable+"("+col.name+")")
            
            if(len(sql_dict[table]) != i): sql_file.write(", ")

        sql_file.write(");\n")
    sql_file.write("\n")

    # Part 2, create data
    tables = [val for val in sql_dict.keys() if "_struct" not in val]
    for table in tables:
        print("Inserting values into", table, "table")

        # Create insert structure
        sql_file.write("INSERT INTO "+table+" (")
        i = 0
        for col in sql_dict[table+"_struct"]:
            i += 1
            sql_file.write(col.name+"")
            if(len(sql_dict[table+"_struct"]) != i): sql_file.write(", ")
        sql_file.write(") ")

        # Insert the values
        sql_file.write("VALUES\n")
        i = 0
        for row in sql_dict[table]:
            i+=1
            j = 0
            sql_file.write("(")
            for k in row:
                j += 1
                sql_file.write(k)
                if j != len(row): sql_file.write(", ")
            if i != len(sql_dict[table]): sql_file.write("),")
            else: sql_file.write(");")
            sql_file.write("\n\n")



    # TODO: Loop through all not _struct lists and create data.

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

# print("Converting non standard data to strings")
# json_content = python_json_standardize(json_content)

print("Converting lists of lists to lists of dicts")
json_content = python_dict_list_list_convert(json_content)

print("Mapping SQL structure")
sql_dict = create_sql_dict_from_json(json_content, "main")
sql_dict = create_sql_data_from_json(json_content, sql_dict, "main")
print_sql_struct(sql_dict)


print("Creating Output")
sql_out = open("output.sql", "w")
create_mysql_struct_from_dict(sql_dict, sql_out)
sql_out.close()




