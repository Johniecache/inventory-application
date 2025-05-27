import io
import csv
import json
import pandas as pd
from utilities import pad_inventory, generate_all_drawer_keys
from Logger import Logger

class ImportManager:
    """handles the process of importing data from specific file types into the inventory.
    """
    def __init__(self, inventory_manager, pad_func):
        """constructor for class.

        Args:
            inventory_manager (class): instance of inventory manager.
            pad_func (class): instance of pad function.
        """
        self.inventory_manager = inventory_manager # initializes the inventory manager instance
        self.pad_inventory = pad_func # initializes the pad function

    def import_csv(self, file, cabinet):
        """imports inventory data from a CSV file into a specific cabinet.

        Args:
            file (werkzeug.datastructures.FileStorage): the uploaded CSV file.
            cabinet (str): the name of the cabinet to import data into.

        Returns:
            bool: true if import was successful, false otherwise.
        """
        try: # handles errors during the import process
            stream = io.StringIO(file.stream.read().decode("UTF8")) # reads the file content into a string stream
            reader = csv.reader(stream) # creates a CSV reader object
            header = next(reader, None) # reads the header row, if any

            # determine column indices
            id_col, name_col, qty_col = -1, -1, -1 # initializes column indices to -1
            if header: # if a header exists
                try: # handles errors during header parsing
                    id_col = header.index('ID') # finds the index of 'ID' column
                    name_col = header.index('Name') # finds the index of 'Name' column
                    qty_col = header.index('Quantity') # finds the index of 'Quantity' column
                except ValueError: # if a column is not found
                    Logger.warning("csv header missing expected columns (id, name, quantity). attempting import by position.") # logs a warning
            
            if id_col == -1 or name_col == -1 or qty_col == -1: # if headers were not found or incomplete, assume fixed positions
                Logger.info("importing csv by column position (0:id, 1:name, 2:quantity)") # logs that import is by position

            for i, row in enumerate(reader): # iterates through each row in the CSV
                if not row: # skips empty rows
                    continue # continues to the next row
                try: # handles errors for individual row processing
                    drawer_id = row[id_col].strip().upper() if id_col != -1 and len(row) > id_col else row[0].strip().upper() # gets drawer ID from header-defined index or first column
                    name = row[name_col].strip() if name_col != -1 and len(row) > name_col else row[1].strip() if len(row) > 1 else "" # gets name from header-defined index or second column
                    qty = int(row[qty_col].strip()) if qty_col != -1 and len(row) > qty_col else int(row[2].strip()) if len(row) > 2 else 0 # gets quantity from header-defined index or third column
                    
                    self.inventory_manager.update_drawer(drawer_id, name, qty, cabinet) # updates the drawer in the inventory
                except (IndexError, ValueError) as e: # catches errors for malformed rows
                    Logger.warning(f"skipping malformed csv row {i+1}: '{row}' for cabinet '{cabinet}': {e}") # logs a warning for malformed row
                    continue # continues to the next row
            Logger.info(f"csv import successful for cabinet '{cabinet}'") # logs a success message
            return True # returns true indicating successful import
        except Exception as e: # catches any exception during import
            Logger.error(f"csv import failed for cabinet '{cabinet}': {e}") # logs an error message
            return False # returns false indicating failed import

    def import_json(self, file, cabinet):
        """imports inventory data from a JSON file into a specific cabinet.

        Args:
            file (werkzeug.datastructures.FileStorage): the uploaded JSON file.
            cabinet (str): the name of the cabinet to import data into.

        Returns:
            bool: true if import was successful, false otherwise.
        """
        try: # handles errors during the import process
            data = json.load(file.stream) # loads JSON data from the file stream
            if not isinstance(data, dict): # checks if the loaded data is not a dictionary
                Logger.error(f"invalid json format for cabinet '{cabinet}': expected a dictionary") # logs an error
                return False # returns false for invalid format

            for drawer_id, details in data.items(): # iterates through each item in the JSON data
                try: # handles errors for individual drawer processing
                    name = details.get('name', '').strip() # gets the name from details
                    qty = int(details.get('qty', 0)) # gets the quantity from details
                    self.inventory_manager.update_drawer(drawer_id.upper(), name, qty, cabinet) # updates the drawer in the inventory
                except (ValueError, TypeError) as e: # catches errors for invalid name or quantity
                    Logger.warning(f"skipping malformed json entry for drawer '{drawer_id}' in cabinet '{cabinet}': {e}") # logs a warning
                    continue # continues to the next entry
            Logger.info(f"json import successful for cabinet '{cabinet}')") # logs a success message
            return True # returns true indicating successful import
        except Exception as e: # catches any exception during import
            Logger.error(f"json import failed for cabinet '{cabinet}': {e}") # logs an error message
            return False # returns false indicating failed import

    def import_txt(self, file, cabinet):
        """imports inventory data from a plain text file into a specific cabinet.
        expected format: "id: name (quantity)" or "id,name,quantity" or "name,quantity"

        Args:
            file (werkzeug.datastructures.FileStorage): the uploaded TXT file.
            cabinet (str): the name of the cabinet to import data into.

        Returns:
            bool: true if import was successful, false otherwise.
        """
        try: # handles errors during the import process
            content = file.stream.read().decode("UTF8") # reads the file content into a string
            lines = content.splitlines() # splits the content into individual lines

            for i, line in enumerate(lines): # iterates through each line
                line = line.strip() # strips whitespace from the line
                if not line: # skips empty lines
                    continue # continues to the next line

                drawer_id, name, qty = None, "", 0 # initializes variables

                # try parsing "id: name (quantity)"
                if ':' in line and '(' in line and ')' in line: # checks for the specific format
                    try: # handles errors during parsing
                        parts = line.split(':') # splits by colon
                        drawer_id_part = parts[0].strip().upper() # gets drawer id part
                        name_qty_part = ":".join(parts[1:]).strip() # gets name and quantity part
                        
                        name_start = name_qty_part.find('(') # finds the start of quantity
                        name_end = name_qty_part.rfind(')') # finds the end of quantity

                        if name_start != -1 and name_end != -1 and name_end > name_start: # if quantity is found
                            name = name_qty_part[:name_start].strip() # extracts name
                            qty = int(name_qty_part[name_start+1:name_end].strip()) # extracts and converts quantity
                            drawer_id = drawer_id_part # sets drawer id
                        else: # if quantity is not found in expected format
                            Logger.warning(f"txt import: quantity not found in expected format for line {i+1}: '{line}'") # logs a warning
                    except (ValueError, IndexError) as e: # catches errors during parsing
                        Logger.warning(f"txt import: failed to parse 'id: name (qty)' format for line {i+1}: '{line}': {e}") # logs a warning
                
                # try parsing "id,name,quantity" or "name,quantity"
                if drawer_id is None: # if not parsed by the first method
                    parts = [p.strip() for p in line.split(',')] # splits by comma
                    try: # handles errors during parsing
                        if len(parts) == 3: # if 3 parts (id, name, quantity)
                            drawer_id = parts[0].upper() # sets drawer id
                            name = parts[1] # sets name
                            qty = int(parts[2]) # sets quantity
                        elif len(parts) == 2: # if 2 parts (name, quantity)
                            # try to find drawer by name if it exists, otherwise assign to first unused key
                            potential_name = parts[0] # sets potential name
                            potential_qty = int(parts[1]) # sets potential quantity
                            
                            # check if potential_name is an existing drawer id
                            if potential_name.upper() in self.inventory_manager.get_inventory(cabinet): # if it's an existing drawer id
                                drawer_id = potential_name.upper() # sets drawer id
                                name = self.inventory_manager.get_drawer(drawer_id, cabinet).get('name', '') # gets existing name
                                qty = potential_qty # sets quantity
                            else: # if not an existing drawer id, treat as name
                                # find by name first
                                current_inventory = self.inventory_manager.get_inventory(cabinet) # gets current inventory
                                matched_id = next((k for k, v in current_inventory.items() if v.get('name', '').lower() == potential_name.lower()), None) # finds matching drawer by name
                                if matched_id: # if a match is found
                                    drawer_id = matched_id # sets drawer id
                                    name = potential_name # sets name
                                    qty = potential_qty # sets quantity
                                else: # if no match by name, try to assign to an unused key
                                    all_keys = generate_all_drawer_keys() # generates all possible drawer keys
                                    used_keys = set(current_inventory.keys()) # gets used keys
                                    available_keys = sorted(list(set(all_keys) - used_keys)) # finds available keys
                                    if available_keys: # if available keys exist
                                        drawer_id = available_keys[0] # assigns to the first available key
                                        name = potential_name # sets name
                                        qty = potential_qty # sets quantity
                                    else: # if no available keys
                                        Logger.warning(f"txt import: no available drawer id for line {i+1}: '{line}' in cabinet '{cabinet}'") # logs a warning
                                        continue # skips to the next line
                        else: # if not 2 or 3 parts
                            Logger.warning(f"txt import: skipping malformed line {i+1}: '{line}' for cabinet '{cabinet}'") # logs a warning
                            continue # skips to the next line
                    except (ValueError, IndexError) as e: # catches errors during parsing
                        Logger.warning(f"txt import: failed to parse comma-separated format for line {i+1}: '{line}': {e}") # logs a warning
                        continue # skips to the next line

                if drawer_id: # if a drawer id was successfully determined
                    self.inventory_manager.update_drawer(drawer_id, name, qty, cabinet) # updates the drawer in the inventory
                else: # if no drawer id could be determined
                    Logger.warning(f"txt import: unable to determine drawer id for line {i+1}: '{line}' in cabinet '{cabinet}'") # logs a warning
            
            Logger.info(f"txt import successful for cabinet '{cabinet}'") # logs a success message
            return True # returns true indicating successful import
        except Exception as e: # catches any exception during import
            Logger.error(f"txt import failed for cabinet '{cabinet}': {e}") # logs an error message
            return False # returns false indicating failed import

    def import_excel(self, file, cabinet):
        """imports inventory data from an Excel (XLSX) file into a specific cabinet.

        Args:
            file (werkzeug.datastructures.FileStorage): the uploaded Excel file.
            cabinet (str): the name of the cabinet to import data into.

        Returns:
            bool: true if import was successful, false otherwise.
        """
        try: # handles errors during the import process
            df = pd.read_excel(file.stream) # reads the Excel file into a pandas dataframe
            
            # expected columns: 'id', 'name', 'quantity'
            if not all(col in df.columns for col in ['ID', 'Name', 'Quantity']): # checks if essential columns are missing
                Logger.error(f"excel import failed for cabinet '{cabinet}': missing required columns (id, name, quantity)") # logs an error
                return False # returns false for missing columns

            for index, row in df.iterrows(): # iterates through each row in the dataframe
                try: # handles errors for individual row processing
                    drawer_id = str(row['ID']).strip().upper() # gets drawer id, converts to string and uppercase
                    name = str(row['Name']).strip() # strip name
                    if name.lower() == 'nan': # check if the string representation is 'nan' (case-insensitive)
                        name = '' # convert to empty string
                    
                    qty = int(row['Quantity']) # gets quantity, converts to integer
                    
                    self.inventory_manager.update_drawer(drawer_id, name, qty, cabinet) # updates the drawer in the inventory
                except (ValueError, TypeError) as e: # catches errors for invalid data types in row
                    Logger.warning(f"skipping malformed excel row {index+1}: {row.to_dict()} for cabinet '{cabinet}': {e}") # logs a warning
                    continue # continues to the next row
            Logger.info(f"excel import successful for cabinet '{cabinet}'") # logs a success message
            return True # returns true indicating successful import
        except Exception as e: # catches any exception during import
            Logger.error(f"excel import failed for cabinet '{cabinet}': {e}") # logs an error message
            return False # returns false indicating failed import