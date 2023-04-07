"""
Author: Jay Barot
Organization: Special Collections, Vanderbilt University
Date: 04/07/2023
"""

# import the required modules
import logging
import argparse
import csv
import xlrd
import json

class Cortex2JStore:
        
    """
    Constructor
    """
    def __init__(self, logger):
        self.logger = logger # Logger object
        self.cortex = None # Cortex data
        self.jstore = None # JStore data

    
    """
    Configure
    """
    def configure(self, args):
        try:
            self.logger.info("Cortex2JStore::configure")

            # Initialize the data structures
            self.cortex = []
            self.jstore = []

            # Convert the raw files to internal data structures
            self.raw2data(path = args.cortex_raw, type = "csv", savein = "cortex", op_ref_required = True)
            self.raw2data(path = args.jstore_raw, type = "xls", savein = "jstore", op_ref_required = True)


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

        
        except Exception as e:
            self.logger.error("Cortex2JStore::driver: Exception: " + str(e))
            raise e
    

    def raw2data (self, path, type, savein, op_ref_required = False):
        try:
            self.logger.info("Cortex2JStore::raw2data")

            # Map string values to variable names using a dictionary
            var_dict = {
                'cortex': self.cortex,
                'jstore': self.jstore,
            }

            if type == "csv":
                # Read the CSV file
                with open(path, 'r') as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    for row in csv_reader:
                        var_dict.get(savein).append(row)

            elif type == "xls":
                # Read the XLS file
                workbook = xlrd.open_workbook(path)
                worksheet = workbook.sheet_by_index(0)
                headers = [cell.value for cell in worksheet.row(0)]
                for i in range(1, worksheet.nrows):
                    row_data = {}
                    for j in range(len(headers)):
                        row_data[headers[j]] = worksheet.cell_value(i, j)
                    
                    var_dict.get(savein).append(row)
            
            else:
                raise Exception("Unknown file type")


            if op_ref_required:
                # Export the data to a JSON file
                with open('output/'+ savein +'.json', 'w') as json_file:
                    json.dump(var_dict.get(savein), json_file, indent=4)
        

        except Exception as e:
            self.logger.error("Cortex2JStore::raw2data: Exception: " + str(e))
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

  parser.add_argument ("-c", "--cortex_raw", type=str, default="data/cortex.csv", help="cortex csv raw file: default cortex.csv")

  parser.add_argument ("-j", "--jstore_raw", type=str, default="data/jstore.xls", help="jstore xls raw file: default jstore.xls")
  
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