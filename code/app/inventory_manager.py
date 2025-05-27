import os
import sqlite3
from Logger import Logger

class InventoryManager:
    """manages inventory data stored in an sqlite database, including CRUD operations, and undo/redo functionality.
    """
    def __init__(self, db_path=None):
        """initializes the InventoryManager, setting up the database path and action history.

        Args:
            db_path (str, optional): the path to the sqlite database file. Defaults to None, which means a default path will be constructed.
        """
        if db_path is None: # checks if a database path was not provided
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # gets the absolute path to the parent directory of the current file
            db_path = os.path.join(base_dir, 'resources', 'database.db') # constructs the default database path
        self.db_path = db_path # sets the database path for the instance
        self.action_history = [] # initializes an empty list to store action history for undo/redo
        self.redo_stack = [] # initializes an empty list to store actions for redo
        Logger.info(f"inventorymanager initialized with db path: {self.db_path}") # logs that the inventory manager has been initialized
        self._initialize_db() # calls a private method to ensure the database and table exist

    def _initialize_db(self):
        """ensures the sqlite database file and the 'drawers' table exist, creating them if necessary.

        Raises:
            Exception: if there is an error during database initialization.
        """
        try: # handles errors during database initialization
            conn = self._connect() # establishes a connection to the database
            c = conn.cursor() # creates a cursor object to execute sql commands
            c.execute('''
                CREATE TABLE IF NOT EXISTS drawers (
                    cabinet TEXT NOT NULL DEFAULT 'Default',
                    row TEXT NOT NULL,
                    column TEXT NOT NULL,
                    name TEXT,
                    qty INTEGER,
                    PRIMARY KEY (cabinet, row, column)
                )
            ''') # executes a sql command to create the 'drawers' table if it doesn't already exist
            conn.commit() # commits the transaction to save changes to the database
            conn.close() # closes the database connection
            Logger.info("database and 'drawers' table ensured to exist with 'cabinet' column.") # logs a success message
        except Exception as e: # catches any exception that occurs
            Logger.error(f"error initializing database: {e}") # logs an error message with the exception details
            raise # re-raises the exception

    def _connect(self):
        """establishes a connection to the sqlite database.

        Raises:
            Exception: if the connection to the database fails.

        Returns:
            sqlite3.Connection: a connection object to the sqlite database.
        """
        try: # handles errors during database connection
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True) # creates the directory for the database file if it doesn't exist
            Logger.debug(f"connecting to db at {self.db_path}") # logs a debug message indicating the database path
            conn = sqlite3.connect(self.db_path) # establishes a connection to the sqlite database
            return conn # returns the database connection object
        except Exception as e: # catches any exception that occurs during connection
            Logger.error(f"failed to connect to db: {e}") # logs an error message with the exception details
            raise # re-raises the exception

    def get_inventory(self, cabinet):
        """retrieves the inventory for a specific cabinet from the database.

        Args:
            cabinet (str): the name of the cabinet to retrieve inventory for.

        Returns:
            dict: a dictionary representing the inventory, with drawer IDs as keys and their details (name, quantity) as values.
        """
        try: # handles errors during inventory retrieval
            conn = self._connect() # establishes a connection to the database
            c = conn.cursor() # creates a cursor object
            c.execute("SELECT row, column, name, qty FROM drawers WHERE cabinet = ?", (cabinet,)) # executes a query to select drawer details for the specified cabinet
            rows = c.fetchall() # fetches all matching rows
            conn.close() # closes the database connection

            inventory = {} # initializes an empty dictionary to store the inventory
            for row, column, name, qty in rows: # iterates through each fetched row
                key = f"{row}{column}" # constructs the drawer ID (e.g., "A1")
                inventory[key.upper()] = {"name": name or "", "qty": qty or 0} # adds the drawer to the inventory dictionary, converting key to uppercase and handling potential None values
            return inventory # returns the constructed inventory dictionary
        except Exception as e: # catches any exception that occurs
            Logger.error(f"error getting inventory for cabinet '{cabinet}': {e}") # logs an error message
            return {} # returns an empty dictionary in case of an error

    def get_drawer(self, drawer_id, cabinet):
        """retrieves the details of a specific drawer from the database.

        Args:
            drawer_id (str): the ID of the drawer (e.g., "A1").
            cabinet (str): the name of the cabinet where the drawer is located.

        Returns:
            dict: a dictionary containing the name and quantity of the drawer, or default empty values if not found or an error occurs.
        """
        if not drawer_id or len(drawer_id) < 2: # checks if the drawer_id is invalid
            Logger.warning(f"invalid drawer_id provided to get_drawer: '{drawer_id}'") # logs a warning for an invalid drawer ID
            return {"name": "", "qty": 0} # returns default empty values for an invalid ID
        row, column = drawer_id[0].upper(), drawer_id[1:] # separates the row character and column number from the drawer ID, converting row to uppercase
        try: # handles errors during drawer retrieval
            conn = self._connect() # establishes a connection to the database
            c = conn.cursor() # creates a cursor object
            c.execute("SELECT name, qty FROM drawers WHERE row = ? AND column = ? AND cabinet = ?", (row, column, cabinet)) # executes a query to select the name and quantity for the specified drawer
            result_row = c.fetchone() # fetches the first matching row
            conn.close() # closes the database connection
            if result_row: # checks if a result row was found
                return {"name": result_row[0] or "", "qty": result_row[1] or 0} # returns the drawer's name and quantity, handling potential None values
            return {"name": "", "qty": 0} # returns default empty values if the drawer is not found
        except Exception as e: # catches any exception that occurs
            Logger.error(f"error getting drawer '{drawer_id}' in cabinet '{cabinet}': {e}") # logs an error message
            return {"name": "", "qty": 0} # returns default empty values in case of an error

    def _update_drawer_in_db(self, drawer_id, name, qty, cabinet):
        """updates or inserts a drawer's details in the database. This is a private helper method.

        Args:
            drawer_id (str): the ID of the drawer (e.g., "A1").
            name (str): the new name for the drawer.
            qty (int): the new quantity for the drawer.
            cabinet (str): the name of the cabinet where the drawer is located.

        Raises:
            Exception: if the database update fails.
        """
        if not drawer_id or len(drawer_id) < 2: # checks if the drawer_id is invalid
            Logger.warning(f"invalid drawer_id provided to _update_drawer_in_db: '{drawer_id}'") # logs a warning for an invalid drawer ID
            return # exits the function if the drawer ID is invalid
        row_char, column_num = drawer_id[0].upper(), drawer_id[1:] # separates the row character and column number, converting row to uppercase
        try: # handles errors during database update
            conn = self._connect() # establishes a connection to the database
            c = conn.cursor() # creates a cursor object
            c.execute( # executes an sql command to insert or replace a drawer's data
                "INSERT OR REPLACE INTO drawers (cabinet, row, column, name, qty) VALUES (?, ?, ?, ?, ?)", # sql statement to insert or replace
                (cabinet, row_char, column_num, name, qty) # parameters for the sql statement
            )
            conn.commit() # commits the transaction to save changes
            conn.close() # closes the database connection
        except Exception as e: # catches any exception that occurs
            Logger.error(f"failed to update drawer '{drawer_id}' in cabinet '{cabinet}' in db: {e}") # logs an error message
            raise # re-raises the exception

    def update_drawer(self, drawer_id, new_name, new_qty, cabinet='Default'):
        """updates a drawer's details and records the action for undo/redo.

        Args:
            drawer_id (str): the ID of the drawer (e.g., "A1").
            new_name (str): the new name for the drawer.
            new_qty (int): the new quantity for the drawer.
            cabinet (str, optional): the name of the cabinet where the drawer is located. Defaults to 'Default'.

        Raises:
            Exception: if the drawer update operation fails.
        """
        Logger.debug(f"attempting to update drawer {drawer_id} in cabinet '{cabinet}' to name '{new_name}', qty {new_qty}") # logs a debug message for the update attempt
        try: # handles errors during the update process
            old = self.get_drawer(drawer_id, cabinet) # retrieves the current details of the drawer
            is_new = (old['name'] == '' and old['qty'] == 0) # checks if the drawer is currently empty (considered "new" for action recording)

            action_data = { # prepares a dictionary to store action details
                'id': drawer_id, # stores the drawer ID
                'cabinet': cabinet, # stores the cabinet name
                'prev_name': old['name'], # stores the previous name of the drawer
                'prev_qty': old['qty'], # stores the previous quantity of the drawer
                'new_name': new_name, # stores the new name for the drawer
                'new_qty': new_qty # stores the new quantity for the drawer
            }

            if is_new: # checks if it's a new drawer being added (from an empty state)
                action_data['type'] = 'delete' # marks the action type as 'delete' for undo purposes (to revert to empty)
                Logger.debug(f"recorded delete action for new drawer {drawer_id} in cabinet '{cabinet}'") # logs the recorded action type
            else: # if it's an existing drawer
                action_data['type'] = 'update' # marks the action type as 'update'
                Logger.debug(f"recorded update action for drawer {drawer_id} in cabinet '{cabinet}'") # logs the recorded action type

            self._record_action(action_data) # records the action for undo/redo

            self._update_drawer_in_db(drawer_id, new_name, new_qty, cabinet) # updates the drawer in the database
            Logger.info(f"updated drawer {drawer_id} in cabinet '{cabinet}' in db to name '{new_name}', qty {new_qty}") # logs a success message for the database update
        except Exception as e: # catches any exception that occurs during the update
            Logger.error(f"error updating drawer '{drawer_id}' in cabinet '{cabinet}': {e}") # logs an error message
            raise # re-raises the exception

    def _record_action(self, action):
        """records an action in the history and clears the redo stack.

        Args:
            action (dict): a dictionary containing the details of the action performed.
        """
        self.action_history.append(action) # adds the action to the action history list
        self.redo_stack.clear() # clears the redo stack because a new action invalidates future redos

    def clear_inventory(self):
        """clears all inventory data from the database.

        Raises:
            Exception: if clearing the inventory fails.
        """
        try: # handles errors during inventory clearing
            conn = self._connect() # establishes a connection to the database
            c = conn.cursor() # creates a cursor object
            c.execute("DELETE FROM drawers") # executes a sql command to delete all rows from the 'drawers' table
            conn.commit() # commits the transaction
            conn.close() # closes the database connection
            Logger.info("inventory database cleared (all cabinets).") # logs a success message
        except Exception as e: # catches any exception that occurs
            Logger.error(f"failed to clear inventory: {e}") # logs an error message
            raise # re-raises the exception

    def undo(self):
        """reverts the last performed action.

        Returns:
            bool: true if the undo operation was successful, false otherwise.
        """
        if not self.action_history: # checks if the action history is empty
            Logger.warning("undo called but action history is empty") # logs a warning if there's nothing to undo
            return False # returns false if no actions to undo

        action = self.action_history.pop() # retrieves and removes the last action from the history
        Logger.debug(f"undoing action: {action}") # logs the action being undone

        try: # handles errors during the undo operation
            cabinet_for_undo = action.get('cabinet', 'Default') # gets the cabinet name for the action, defaulting to 'Default'
            if action['type'] == 'update': # checks if the action was an 'update'
                self._update_drawer_in_db(action['id'], action['prev_name'], action['prev_qty'], cabinet_for_undo) # reverts the drawer to its previous state
            elif action['type'] == 'delete': # checks if the action was a 'delete' (meaning a new drawer was added)
                self._update_drawer_in_db(action['id'], '', 0, cabinet_for_undo) # "deletes" the newly added drawer by setting its name and qty to empty/zero
            
            self.redo_stack.append(action) # adds the undone action to the redo stack
            Logger.info(f"undo successful for drawer {action['id']} in cabinet '{cabinet_for_undo}'") # logs a success message
            return True # returns true indicating successful undo
        except Exception as e: # catches any exception that occurs during undo
            Logger.error(f"undo failed: {e}") # logs an error message
            return False # returns false if undo failed

    def redo(self):
        """re-applies the last undone action.

        Returns:
            bool: true if the redo operation was successful, false otherwise.
        """
        if not self.redo_stack: # checks if the redo stack is empty
            Logger.warning("redo called but redo stack is empty") # logs a warning if there's nothing to redo
            return False # returns false if no actions to redo

        action = self.redo_stack.pop() # retrieves and removes the last action from the redo stack
        Logger.debug(f"redoing action: {action}") # logs the action being redone

        try: # handles errors during the redo operation
            cabinet_for_redo = action.get('cabinet', 'Default') # gets the cabinet name for the action, defaulting to 'Default'
            self._update_drawer_in_db(action['id'], action['new_name'], action['new_qty'], cabinet_for_redo) # re-applies the action by setting the drawer to its new state
            self.action_history.append(action) # adds the redone action back to the action history
            Logger.info(f"redo successful for drawer {action['id']} in cabinet '{cabinet_for_redo}'") # logs a success message
            return True # returns true indicating successful redo
        except Exception as e: # catches any exception that occurs during redo
            Logger.error(f"redo failed: {e}") # logs an error message
            return False # returns false if redo failed
    
    def get_all_cabinets(self):
        """retrieves a list of all unique cabinet names from the database.

        Returns:
            list: a sorted list of unique cabinet names.
        """
        try: # handles errors during cabinet retrieval
            conn = self._connect() # establishes a connection to the database
            cursor = conn.cursor() # creates a cursor object
            cursor.execute("SELECT DISTINCT cabinet FROM drawers") # executes a query to select all unique cabinet names
            results = cursor.fetchall() # fetches all matching results
            conn.close() # closes the database connection
            return sorted([r[0] for r in results if r[0]]) # extracts cabinet names, filters out empty strings, and returns a sorted list
        except Exception as e: # catches any exception that occurs
            Logger.error(f"failed to get all cabinets: {e}") # logs an error message
            return [] # returns an empty list in case of an error
