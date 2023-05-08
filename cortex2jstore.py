"""
Author: Jay Barot
Organization: Special Collections, Vanderbilt University
Date: 04/07/2023
"""

# import the required modules
from config import match_columns
from config import jstore_schema_columns
import logging
import argparse
import csv
import xlrd
import json
import time
import pandas as pd
import openpyxl

class Cortex2JStore:
        
    """
    Constructor
    """
    def __init__(self, logger):
        self.logger = logger # Logger object
        self.cortex = None # Cortex data
        self.jstore = None # JStore data
        self.matches = None # Matches between Cortex and JStore
    
    """
    Configure
    """
    def configure(self, args):
        try:
            self.logger.info("Cortex2JStore::configure")

            # Initialize the data structures
            self.cortex = []
            self.jstore = []
            self.matches = []
            self.final_jstore = []

            # Map string values to variable names (our internal datastructure in this case) using a dictionary
            self.var_dict = {
                'cortex': self.cortex,
                'jstore': self.jstore,
                'matches': self.matches
            }

            # Convert the raw files to internal data structures
            self.raw2data(path = args.cortex_raw, type = "csv", target = "cortex", is_2bexported = False)
            self.raw2data(path = args.jstore_raw, type = "xls", target = "jstore", is_2bexported = True)

        except Exception as e:
            self.logger.error("Cortex2JStore::configure: Exception: " + str(e))
            raise e
    

    """
    Main driver method
    """
    def driver (self):
        try:
            self.logger.info("Cortex2JStore::driver")

            # dump the configuration
            self.dump ()  
                        
            # Clean up and export the Cortex data
            self.cortex_cleanup()
            self.export_data(data = self.cortex, path = 'output/cortex.json', type = 'json')
            
            # Find the matches
            self.find_matches()
            self.export_data(data = self.matches, path = 'output/matches.json', type = 'json')

            # Combine the matches
            self.combine_matches()
            self.export_data(data = self.matches, path = 'output/combined.json', type = 'json')

            # Remove the cortex data from the combined matches
            # The result of this operation will be the final JStore data that 
            # needs to be standardized according to JStore schema requirements.
            self.remove_cortex_data()
            self.export_data(data = self.final_jstore, path = 'output/nsjstore.json', type='json')

            self.standardize_jstore()
            self.export_data(data = self.final_jstore, path = 'output/finaljstore.json', type='json')

            # Export the local subjects list
            uniquelocalsubjects = self.getlocalsubjectslist()
            list_uniquelocalsubjects = list(uniquelocalsubjects)
            self.export_data(data = list_uniquelocalsubjects, path = 'output/localsubjects.json', type='json')
            df = pd.DataFrame(list_uniquelocalsubjects, columns=["Local Subjects"])
            df.to_excel("output/localsubjects.xlsx", index=False)

            # Export the final JStore data in XLSX format
            self.export_data(data = self.final_jstore, path = 'output/finaljstore.xlsx', type = 'xlsx')

        except Exception as e:
            self.logger.error("Cortex2JStore::driver: Exception: " + str(e))
            raise e
    

    def find_matches(self):
        try:
            self.logger.info("Cortex2JStore::find_matches: Finding matches between Cortex and JStore")

            start_time = time.time()

            # Create a dictionary of "Original File Name" values from cortex
            cortex_dict = {c["Original File Name"]: c for c in self.cortex}

            # Iterate over jstore and check for matches with cortex_dict
            for j in self.jstore:
                c = cortex_dict.get(j["Filename"])
                if c:
                    self.matches.append((j, c))
            
            end_time = time.time()

            self.logger.info("Matches alogrithm took : " + str(end_time - start_time) + " seconds")
        
        except Exception as e:
            self.logger.error("Cortex2JStore::find_matches: Exception: " + str(e))
            raise e
    

    def combine_matches (self):
        try:
            self.logger.info("Cortex2Jstore::combine_matches: Combining matches")

            # Iterator over the matching records
            for match in self.matches:
                
                # Iterate over the match_columns dictionary
                # and update the jstore with cortex column data.
                for k, v in match_columns.items():
                    
                    # Check if the value is empty in the jstore data, 
                    # as we do not want to overwrite the existing data.
                    # with cortex data
                    if match[0][k] == "":
                        match[0][k] = match[1][v]
        
        except Exception as e:
            self.logger.error("Cortex2Jstore::combine_matches: Exception: " + str(e))
            raise e
    

    """
    This method is used to remove the cortex data from the combined matches.
    """
    def remove_cortex_data (self):
        try:
            self.logger.info("Cortex2Jstore::remove_cortex_data: Removing cortex data from combined matches")
            
            self.final_jstore = []

            # Iterate over the combined matches and remove the cortex data
            for match in self.matches:
                self.final_jstore.append(match[0])
                
        except Exception as e:
            self.logger.error("Cortex2Jstore::remove_cortex_data: Exception: " + str(e))
            raise e
    

    """
    This method is used to convert the final data to the required schema format by JStore.
    We go through each column that needed to be reformatted according to JStore schema.
    We defined these columns in the config file.
    """
    def standardize_jstore (self):
        try:
            self.logger.info("Cortex2Jstore::standardize_jstore: Standardizing JStore data")

            for row in self.final_jstore:
                for k, v in row.items():
                    
                    # Select columns to be reformatted
                    if k in jstore_schema_columns:
                        """
                        Setup the pipeline 
                        """

                        # Replace commas with pipes
                        row[k] = self.comma_replace_pipe(v)

                        # If the key is "Vanderbilt People[2083840]"
                        # then we need to standardize the naming convention <LastName, FirstName + Extra>
                        if k == "Vanderbilt People[2083840]":
                            row[k] = self.standardize_vanderbilt_people(row[k])
                            # self.standardize_vanderbilt_people(row[k])
        
        except Exception as e:
            self.logger.error("Cortex2Jstore::standardize_jstore: Exception: " + str(e))
            raise e
    

    """
    This method will replace the commas with pipes in the given string, only if there
    is no space before and after the comma.

    Parameters:
    :param string: String to be processed
    :ptype string: str
    """
    def comma_replace_pipe (self, string):
        try:
            self.logger.debug("Cortex2Jstore::comma_replace_pipe: replacing commas with pipes")

            new_string = ""

            for i in range(len(string)):
                if string[i] == ",":
                    if string[i-1] != " " and string[i+1] != " ":
                        new_string += "|"
                    else:
                        new_string += ","
                else:
                    new_string += string[i]

            return new_string
        
        except Exception as e:
            self.logger.error("Cortex2Jstore::comma_replace_pipe: Exception: " + str(e))
            raise e
    

    def standardize_vanderbilt_people (self, string):
        try:
            self.logger.debug("Cortex2Jstore::standardize_vanderbilt_people: Standardizing Vanderbilt People")

            # Split the string by pipe
            values_list = string.split('|')
            new_values_list = []
            for name in values_list:
                formatted_name = self.format_name(name)
                if formatted_name != "":
                    new_values_list.append(self.format_name(name))
            
            formatted_names =  '|'.join(new_values_list)

            # self.logger.debug("#########################################################")
            # self.logger.debug("Cortex2Jstore::standardize_vanderbilt_people: values_list: \n" + str(values_list))
            # self.logger.debug("Cortex2Jstore::standardize_vanderbilt_people: formatted_names: \n" + str(formatted_names))
            # self.logger.debug("#########################################################")

            return formatted_names
        
        except Exception as e:
            self.logger.error("Cortex2Jstore::standardize_vanderbilt_people: Exception: " + str(e))
            raise e
    

    def format_name(self, name):
        parts = name.split()

        if len(parts) < 2:
            # Logic: If there is only one part in the name,
            # then return the name as it is.
            return name
        
        elif len(parts) == 2:
            # Logic: If there are two parts in the name,
            # then return the name as <LastName, FirstName>
            return f"{parts[1]}, {parts[0]}"
        
        else:
            # Logic: If there are more than two parts in the name,
            # then first check if the name contains a suffix.
            # If it does, then take the word before the suffix as the last name.
            # and then append whatever is left as the extra.
            # If it does not, then take the last word as the last name.
            suffix_list = ["Jr.", "Sr.", "II.", "III.", "IV.", "V.", "VI.", "VII.", "VIII.", "IX.", "X."]
            has_suffix = False
            suffix_location = 0

            for part in parts:
                if part in suffix_list:
                    has_suffix = True
                    suffix_location = parts.index(part)
                    break
            
            if has_suffix:
                last_name = ''.join(parts[suffix_location - 1])

                extra = ''

                for part in parts:
                    if parts.index(part) != suffix_location - 1:
                        if parts.index(part) != len(parts) - 1:
                            extra += part + ' '
                        else:
                            extra += part
                
                extra_parts = extra.split()

                # Get new suffix location
                suffix_location = 0
                for part in extra_parts:
                    if part in suffix_list:
                        suffix_location = extra_parts.index(part)
                        break
                
                # Divide the extra in two parts
                before_suffix = ''
                after_suffix = ''

                for part in extra_parts:
                    if extra_parts.index(part) < suffix_location:
                        before_suffix += part + ' '
                    else:
                        if extra_parts.index(part) != len(extra_parts) - 1:
                            after_suffix += part + ' '
                        else:
                            after_suffix += part
                
                before_suffix = before_suffix[:-1] + ","
                return f"{last_name}, {before_suffix} {after_suffix}"

            else:
                # We need to check if there is paranthesis in the name
                for s in part[-1]:
                    if ("(" in s) or (")" in s):
                        return f""
                
                last_name = ''.join(parts[-1])
                first_name_plus_extra = ' '.join(parts[:-1])
                return f"{last_name}, {first_name_plus_extra}"

        # else:
        #     first_name = ' '.join(parts[:-2])
        #     last_name = parts[-2]
        #     extra = parts[-1]
        #     return f"{last_name}, {first_name} {extra}"
        

    def getlocalsubjectslist(self):
        try:
            self.logger.info("Cortex2Jstore::getlocalsubjectslist: Getting local subjects list")

            unique_local_subjects = set()

            for row in self.final_jstore:
                for k, v in row.items():
                    
                    # Select columns to be reformatted
                    if k == "Vanderbilt Local Subjects[2083876]":
                        values_list = v.split('|')
                        unique_local_subjects.update(set(values_list))
            
            return unique_local_subjects

        except Exception as e:
            self.logger.error("Cortex2Jstore::getlocalsubjectslist: Exception: " + str(e))
            raise e

    """
    This method converts the raw data into internal data structures

    Parameters:
    :param path: Path to the raw file
    :ptype path: str
    :param type: Type of the raw file
    :ptype type: str
    :param target: Name of the datastructure to save the data in (cortex or jstore)
    :ptype target: str
    :param is_required_reference: Flag to indicate if the data is required for the reference output
    :ptype is_required_reference: bool
    """
    def raw2data (self, path, type, target, is_2bexported= False):
        try:
            self.logger.info("Cortex2JStore::raw2data")
            
            # Read the CSV file
            if type == "csv":
                with open(path, 'r') as csv_file:
                    csv_reader = csv.DictReader(csv_file)

                    for row in csv_reader:
                        self.var_dict.get(target).append(row)

            # Read the XLS file
            elif type == "xls":
                workbook = xlrd.open_workbook(path)
                worksheet = workbook.sheet_by_index(0)
                headers = [cell.value for cell in worksheet.row(0)]

                for i in range(1, worksheet.nrows):
                    row_data = {}
                    for j in range(len(headers)):
                        row_data[headers[j]] = worksheet.cell_value(i, j)
                    self.var_dict.get(target).append(row_data)
            
            else:
                raise Exception("Unknown file type")

            # Export the data
            if is_2bexported: self.export_data(data = self.var_dict.get(target), path = 'output/'+ target +'.json') 

        except Exception as e:
            self.logger.error("Cortex2JStore::raw2data: Exception: " + str(e))
            raise e
    

    def cortex_cleanup(self):
        try:
            self.logger.info("Cortex2JStore::cortex_cleanup")
            
            for item in self.cortex:
                new_keys = {}

                for key in item.keys():

                    # Removing random unicode values
                    new_key = key.replace("\u00ef\u00bb\u00bf", "").replace("\"", "")
                    new_key = key.replace("\ufeff", "").replace("\"", "")

                    # NOTE: redundant_col contains cortex appended field value, CoreField.OriginalFileName
                    new_key, redundant_col = new_key.split("|")
                    new_keys[new_key] = item[key]

                item.clear()
                item.update(new_keys)
        
        except Exception as e:
            self.logger.error("Cortex2JStore::cortex_cleanup: Exception: " + str(e))
            raise e

    """
    Description: exports the data to JSON files

    Parameters:
    :param data: Data to be exported
    :ptype data: dict
    :param path: Path to the JSON file
    :ptype path: str
    """
    def export_data (self, data, path, type = "json"):
        try:
            self.logger.info("Cortex2JStore::export_data")

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

        except Exception as e:
            self.logger.error("Cortex2JStore::export_data: Exception: " + str(e))
            raise e
    

    """
    Dumping Cortex2JStore object configuration information
    """
    def dump (self):
        try:
            self.logger.info ("**********************************")
            self.logger.info ("Cortex2JStore::dump")
            self.logger.info ("------------------------------")
            self.logger.info ("     Log Level: {}".format (self.logger.getEffectiveLevel ()))
            self.logger.info ("**********************************")

        except Exception as e:
            raise e


"""
Parse command line arguments
"""
def parseCmdLineArgs ():
  # instantiate a ArgumentParser object
  parser = argparse.ArgumentParser (description="Cortex2JStore: A program to merge Cortex data into JStore")

  parser.add_argument ("-l", "--loglevel", type=int, default=logging.INFO, choices=[logging.DEBUG,logging.INFO,logging.WARNING,logging.ERROR,logging.CRITICAL], help="logging level, choices 10,20,30,40,50: default 20=logging.INFO")

  parser.add_argument ("-c", "--cortex_raw", type=str, default="data/cortex.csv", help="cortex csv raw file: default data/cortex.csv")

  parser.add_argument ("-j", "--jstore_raw", type=str, default="data/jstore.xls", help="jstore xls raw file: default data/jstore.xls")
  
  return parser.parse_args()


"""
Main program
"""
def main ():
  try:
    # obtain a system wide logger and initialize it to debug level to begin with
    logging.info ("Main - acquire a child logger and then log messages in the child")
    logger = logging.getLogger ("Cortex2JStore")
    
    # first parse the arguments
    logger.debug ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # reset the log level to as specified
    logger.debug ("Main: resetting log level to {}".format (args.loglevel))
    logger.setLevel (args.loglevel)
    logger.debug ("Main: effective log level is {}".format (logger.getEffectiveLevel ()))

    # Obtain the application object 
    logger.debug ("Main: obtain the cortex2jstore appln object")
    appln = Cortex2JStore (logger)

    # configure the object
    logger.debug ("Main: configure the cortex2jstore appln object")
    appln.configure (args)

    # now invoke the driver program
    logger.debug ("Main: invoke the cortex2jstore appln driver")
    appln.driver ()

  except Exception as e:
    logger.error ("Exception caught in main - {}".format (e))
    return
  
  
"""
Main entry point for the program
"""
if __name__ == "__main__":

  # set underlying default logging capabilities
  logging.basicConfig (level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

  main ()