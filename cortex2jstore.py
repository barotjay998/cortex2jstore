"""
Author: Jay Barot
Organization: Special Collections, Vanderbilt University
Date: 04/07/2023
"""

# import the required modules
from config import match_columns
import logging
import argparse
import csv
import xlrd
import json
import time

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
            self.export_data(data = self.cortex, path = 'output/cortex.json')
            
            # Find the matches
            self.find_matches()
            self.export_data(data = self.matches, path = 'output/matches.json')

            # Combine the matches
            self.combine_matches()
            self.export_data(data = self.matches, path = 'output/combined.json')

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
                    new_key = key.replace("\u00ef\u00bb\u00bf", "").replace("\"", "")
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
    def export_data (self, data, path):
        try:
            self.logger.info("Cortex2JStore::export_data")

            with open(path, 'w') as json_file:
                json.dump (data, json_file, indent=4)     

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