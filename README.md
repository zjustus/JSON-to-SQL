# JSON-to-SQL
A Json to SQL converter designed for continuous updating data. 

# Sample Execution
`python3 geojson_import.py data.json`


# Command Line parameters
- input json file name

# Requirements
pip install inquirer

# How it Works
1. Import the JSON file.
2. Map the structure and confirm all fields are correct
3. prompt if this a data refresh or new install
4. prompt user what data needs to be included, all or some.
5. prompt user what fields are the primary keys
6. if data refresh, ask for database credentials and probe to see if new columns need to be created
7. Do the processing and build the SQL file

# Processing - Old
1. Starting at the start, create first table, 
   1. for each field in json, if datatype is not an object, add a column
   2. if datatype is object, flag for new table creation, marking parent table primary key as foreign key in new table
2. call this function recursively? until all fields are mapped,
3. .... (abandoned for lack of structure)


# Processing - Re-imagined.
1. Convert goeJSON into python dictionary
2. Flatten the goeJSON such that any nested dictionaries exist on the first level of the object
3. Check that all lists are uniform, if any data is not, convert all values to a json string. 
4. Convert list of lists into lists of dictionaries
5. Identify structure and log in parser dictionary, appending additional structure for foreign keys
6. Display structure and prompt user for primary keys
7. Recursively traverse every list in every dictionary, append each dictionary to a list with a matching key in parser dictionary
8. Traverse parser dictionary and create tables from {table}_struct keys and Inserts from {table} keys