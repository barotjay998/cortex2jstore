import json
import pandas as pd

"""
Description: exports the data to JSON files

Parameters:
:param data: Data to be exported
:ptype data: dict
:param path: Path to the JSON file
:ptype path: str
"""
def export_data (data, path, type = "json"):
    # Export the data to JSON file
    if type == "json":
        with open(path, 'w') as json_file:
            json.dump (data, json_file, indent=4)
    
    elif type == "xlsx":
        # convert the list of dictionaries to a DataFrame
        df = pd.DataFrame(data)

        # convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(path, index=False)
        
    else:
        raise Exception("Unknown file type")



# Open the JSON file
with open('output/finaljstore.json', 'r') as f:
    # Load the contents of the file into a Python variable
    final_jstore = json.load(f)


# Export the final JStore data in XLSX format
export_data(data = final_jstore, path = 'output/finaljstore.xlsx', type = 'xlsx')