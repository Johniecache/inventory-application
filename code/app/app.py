from flask import Flask, render_template, request, redirect, jsonify, make_response, url_for
import os
import hashlib
import json
import time
import threading
import csv

from inventory_manager import InventoryManager
from system_stats import SystemStats
from export_manager import ExportManager
from import_manager import ImportManager
from utilities import pad_inventory, generate_all_drawer_keys
from Logger import Logger

app = Flask(__name__) # initializes the Flask application
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # defines the absolute path to the project root directory
DB_PATH = os.path.join(PROJECT_ROOT, 'resources', 'database.db') # constructs the full path to the database file

try: # attempts to initialize the InventoryManager
    inventory_manager = InventoryManager(DB_PATH) # creates an instance of InventoryManager with the specified database path
except Exception as e: # catches any exception during initialization
    Logger.error(f"failed to initialize inventorymanager: {e}") # logs an error if initialization fails
    raise # re-raises the exception

try: # attempts to initialize the SystemStats
    system_stats = SystemStats() # creates an instance of SystemStats
except Exception as e: # catches any exception during initialization
    Logger.error(f"failed to initialize systemstats: {e}") # logs an error if initialization fails
    raise # re-raises the exception

try: # attempts to initialize the ExportManager
    export_manager = ExportManager(inventory_manager, pad_inventory) # creates an instance of ExportManager
except Exception as e: # catches any exception during initialization
    Logger.error(f"failed to initialize exportmanager: {e}") # logs an error if initialization fails
    raise # re-raises the exception

try: # attempts to initialize the ImportManager
    import_manager = ImportManager(inventory_manager, pad_inventory) # creates an instance of ImportManager
except Exception as e: # catches any exception during initialization
    Logger.error(f"failed to initialize importmanager: {e}") # logs an error if initialization fails
    raise # re-raises the exception

@app.route('/') # defines the route for the root URL
def index():
    """renders the main inventory page, displaying items for a specific cabinet.

    Args:
        cabinet (str, optional): the name of the cabinet to display. Defaults to 'Default'.

    Returns:
        flask.Response: the rendered HTML template with inventory data.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    try: # attempts to retrieve and pad the inventory
        inventory = inventory_manager.get_inventory(cabinet=cabinet) # retrieves the inventory for the specified cabinet
        inventory = pad_inventory(inventory) # pads the inventory to ensure all drawer keys are present
    except Exception as e: # catches any exception during inventory loading
        Logger.error(f"failed to load inventory for cabinet '{cabinet}': {e}") # logs an error message
        inventory = {} # sets inventory to an empty dictionary in case of an error
    return render_template('index.html', inventory=inventory, cabinet=cabinet) # renders the index.html template with the inventory and cabinet name

@app.route('/clear', methods=['POST']) # defines the route for clearing inventory via a POST request
def clear():
    """clears all inventory data from the database.

    Returns:
        flask.Response: a JSON response indicating success or failure.
    """
    try: # attempts to clear the inventory
        inventory_manager.clear_inventory() # calls the clear_inventory method of the inventory manager
        Logger.info("inventory cleared, redirecting to main page") # logs success and redirect
        return redirect(url_for('index')) # redirects to the main page
    except Exception as e: # catches any exception during the clear operation
        Logger.error(f"failed to clear inventory: {e}") # logs an error message
        return jsonify(success=False, error="failed to clear inventory"), 500 # returns a JSON response with an error and a 500 status code

@app.route('/update', methods=['POST']) # defines the route for updating inventory via a POST request
def update():
    """updates a specific drawer's details in the inventory.

    Returns:
        flask.Response: a JSON response indicating success or failure.
    """
    data = request.get_json() # gets the JSON data from the request body
    Logger.debug(f"received data for update: {data}") # logs the received data for debugging

    if not data: # checks if no data was provided
        Logger.warning("no data provided in update request") # logs a warning
        return jsonify(success=False, error="no data provided"), 400 # returns an error response with a 400 status code

    try: # attempts to validate the quantity
        qty = int(data.get('qty', -1)) # extracts the quantity, defaulting to -1 if not found
        if qty < 0: # checks if the quantity is negative
            raise ValueError("quantity cannot be negative") # raises a ValueError if quantity is negative
    except (ValueError, TypeError) as e: # catches ValueError or TypeError during quantity conversion/validation
        Logger.warning(f"invalid quantity error: {e}") # logs a warning for invalid quantity
        return jsonify(success=False, error="invalid quantity"), 400 # returns an error response with a 400 status code

    drawer_id = data.get('id') # extracts the drawer ID
    name = data.get('name', '').strip() # extracts the name, defaulting to an empty string and stripping whitespace
    cabinet = data.get('cabinet', 'Default') # extracts the cabinet name, defaulting to 'Default'

    if not drawer_id: # checks if the drawer ID is missing
        Logger.warning("drawer id missing in update data") # logs a warning
        return jsonify(success=False, error="drawer id missing"), 400 # returns an error response with a 400 status code

    try: # attempts to update the drawer in the inventory manager
        inventory_manager.update_drawer(drawer_id, name, qty, cabinet) # calls the update_drawer method
        Logger.info(f"updated drawer {drawer_id} in cabinet '{cabinet}' with name '{name}' and qty {qty}") # logs a success message
        return jsonify(success=True) # returns a JSON response indicating success
    except Exception as e: # catches any exception during the database update
        Logger.error(f"db update error: {e}") # logs an error message
        return jsonify(success=False, error="failed to update inventory"), 500 # returns a JSON response with an error and a 500 status code

@app.route('/api/pi-stats') # defines the route for retrieving Raspberry Pi system statistics
def pi_stats():
    """retrieves and returns system statistics.

    Returns:
        flask.Response: a JSON response containing system statistics or an error message.
    """
    try: # attempts to get system statistics
        stats = system_stats.get_all_stats() # calls the get_all_stats method of the system stats manager
        return jsonify(stats) # returns a JSON response with the statistics
    except Exception as e: # catches any exception during statistics retrieval
        Logger.error(f"failed to get pi stats: {e}") # logs an error message
        return jsonify(error="failed to retrieve system stats"), 500 # returns a JSON response with an error and a 500 status code

@app.route('/undo', methods=['POST']) # defines the route for performing an undo operation via a POST request
def undo():
    """performs an undo operation on the last inventory change.

    Returns:
        flask.Response: a JSON response indicating whether the undo was successful.
    """
    try: # attempts to perform an undo
        success = inventory_manager.undo() # calls the undo method of the inventory manager
        return jsonify(success=success) # returns a JSON response indicating success or failure of the undo
    except Exception as e: # catches any exception during the undo operation
        Logger.error(f"undo failed: {e}") # logs an error message
        return jsonify(success=False, error="undo operation failed"), 500 # returns a JSON response with an error and a 500 status code

@app.route('/redo', methods=['POST']) # defines the route for performing a redo operation via a POST request
def redo():
    """performs a redo operation on the last undone inventory change.

    Returns:
        flask.Response: a JSON response indicating whether the redo was successful.
    """
    try: # attempts to perform a redo
        success = inventory_manager.redo() # calls the redo method of the inventory manager
        return jsonify(success=success) # returns a JSON response indicating success or failure of the redo
    except Exception as e: # catches any exception during the redo operation
        Logger.error(f"redo failed: {e}") # logs an error message
        return jsonify(success=False, error="redo operation failed"), 500 # returns a JSON response with an error and a 500 status code

@app.route('/search', methods=['GET']) # defines the route for searching inventory via a GET request
def search():
    """searches the inventory for items matching a given query and renders the results.

    Args:
        cabinet (str, optional): the name of the cabinet to search within. Defaults to 'Default'.
        query (str, optional): the search query. Defaults to an empty string.

    Returns:
        flask.Response: the rendered HTML template with filtered inventory data.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    query = request.args.get('q', '').lower() # gets the 'q' query parameter (search query), converts to lowercase
    try: # attempts to retrieve and pad the full inventory
        full_inventory = inventory_manager.get_inventory(cabinet) # retrieves the full inventory for the specified cabinet
        full_inventory = pad_inventory(full_inventory) # pads the inventory
    except Exception as e: # catches any exception during inventory retrieval
        Logger.error(f"failed to get inventory for search in cabinet '{cabinet}': {e}") # logs an error message
        full_inventory = {} # sets full_inventory to an empty dictionary in case of an error

    filtered_inventory = {} # initializes an empty dictionary for filtered results
    for key, value in full_inventory.items(): # iterates through each item in the full inventory
        try: # handles errors during filtering
            if ( # checks if the query matches the drawer ID, name, or quantity
                query in key.lower() or # checks if query is in lowercase drawer ID
                query in (value.get('name') or '').lower() or # checks if query is in lowercase name (handling None)
                query in str(value.get('qty', '')) # checks if query is in string representation of quantity
            ):
                filtered_inventory[key] = value # adds the matching item to the filtered inventory
        except Exception as e: # catches any exception during filtering an item
            Logger.warning(f"failed filtering inventory item '{key}': {e}") # logs a warning for the failed item
            continue # continues to the next item

    return render_template('index.html', inventory=filtered_inventory, query=query, cabinet=cabinet) # renders the index.html template with filtered inventory

@app.route('/bulk_update', methods=['POST']) # defines the route for performing bulk updates via a POST request
def bulk_update():
    """performs a bulk update of inventory items based on provided text input.

    Args:
        cabinet (str, optional): the name of the cabinet to update. Defaults to 'Default'.
        bulk_input (str): the text input containing lines of inventory data.

    Returns:
        flask.Response: a redirect to the main inventory page after the update.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    text = request.form.get('bulk_input', '') # gets the 'bulk_input' from the form data
    Logger.debug(f"bulk update input for cabinet '{cabinet}':\n{text}") # logs the received bulk update input

    if not text.strip(): # checks if the input text is empty or just whitespace
        Logger.warning(f"bulk update called with empty input for cabinet '{cabinet}'") # logs a warning
        return redirect(f"/?cabinet={cabinet}") # redirects back to the main page if input is empty

    lines = [line.strip() for line in text.splitlines() if line.strip()] # splits the input text into lines, strips whitespace, and filters out empty lines
    try: # attempts to retrieve and pad the inventory
        inventory = inventory_manager.get_inventory(cabinet) # retrieves the inventory for the specified cabinet
        inventory = pad_inventory(inventory) # pads the inventory
    except Exception as e: # catches any exception during inventory loading
        Logger.error(f"failed to load inventory for bulk update in cabinet '{cabinet}': {e}") # logs an error message
        inventory = {} # sets inventory to an empty dictionary in case of an error

    all_keys = generate_all_drawer_keys() # generates a list of all possible drawer keys
    used_keys = set(inventory.keys()) # creates a set of keys currently in use in the inventory
    unused_keys = [k for k in all_keys if k not in used_keys] # finds keys that are not currently used

    for line in lines: # iterates through each line of the bulk input
        parts = [p.strip() for p in line.split(',')] # splits the line by comma and strips whitespace from each part
        try: # handles errors during processing of each line
            if len(parts) == 3: # checks if the line has 3 parts (location, name, qty)
                location, name, qty = parts # unpacks the parts into variables
                qty = int(qty) # converts quantity to an integer
                if qty == 0: # if quantity is 0, clear the drawer
                    inventory_manager.update_drawer(location.upper(), "", 0, cabinet) # updates drawer to empty
                else: # otherwise, update with provided name and quantity
                    inventory_manager.update_drawer(location.upper(), name.strip(), qty, cabinet) # updates drawer
            elif len(parts) == 2: # checks if the line has 2 parts (either location, qty or name, qty)
                first, second = parts # unpacks the parts
                if first.upper() in inventory: # if the first part is an existing drawer ID
                    location = first.upper() # sets location as the uppercase first part
                    qty = int(second) # converts the second part to quantity
                    if qty == 0: # if quantity is 0, clear the drawer
                        inventory_manager.update_drawer(location, "", 0, cabinet) # updates drawer to empty
                    else: # otherwise, update with existing name and new quantity
                        name = inventory[location]['name'] # gets the existing name
                        inventory_manager.update_drawer(location, name, qty, cabinet) # updates drawer
                else: # if the first part is not an existing drawer ID, assume it's a name
                    qty = int(second) # converts the second part to quantity
                    name = first.strip() # sets name as the stripped first part
                    match = next((loc for loc, val in inventory.items() if val.get('name', '').lower() == name.lower()), None) # tries to find a drawer by name
                    if match: # if a matching drawer by name is found
                        if qty == 0: # if quantity is 0, clear the drawer
                            inventory_manager.update_drawer(match, "", 0, cabinet) # updates drawer to empty
                        else: # otherwise, update with existing name and new quantity
                            inventory_manager.update_drawer(match, name, qty, cabinet) # updates drawer
                    else: # if no match by name, try to assign to an unused key
                        all_keys = generate_all_drawer_keys()
                        current_inventory = inventory_manager.get_inventory(cabinet) # get current inventory for available keys
                        used_keys = set(current_inventory.keys())
                        available_keys = sorted(list(set(all_keys) - used_keys))
                        if available_keys:
                            location = available_keys[0]
                            inventory_manager.update_drawer(location, name, qty, cabinet)
                        else:
                            Logger.warning(f"no available drawer id for line '{line}' in cabinet '{cabinet}'")
                            continue
            else: # if the line does not have 2 or 3 parts
                Logger.warning(f"skipping malformed bulk update line: '{line}' for cabinet '{cabinet}'") # logs a warning for malformed line
                continue # skips to the next line

        except Exception as e: # catches any exception during line processing
            Logger.warning(f"failed processing bulk update line '{line}' for cabinet '{cabinet}': {e}") # logs a warning
            continue # continues to the next line

    return redirect(f"/?cabinet={cabinet}") # redirects back to the main page for the current cabinet

@app.route('/api/inventory') # defines the route for retrieving inventory data via API
def get_inventory_api():
    """retrieves and returns inventory data as JSON, with ETag caching.

    Args:
        cabinet (str, optional): the name of the cabinet to retrieve inventory for. Defaults to 'Default'.

    Returns:
        flask.Response: a JSON response containing inventory data, a 304 Not Modified response, or an error.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    try: # attempts to retrieve and process inventory data
        inventory = inventory_manager.get_inventory(cabinet) # retrieves the inventory for the specified cabinet
        inventory = pad_inventory(inventory) # pads the inventory
        inventory_json = json.dumps(inventory, sort_keys=True) # converts the inventory dictionary to a JSON string, sorted by keys
        etag = hashlib.md5(inventory_json.encode()).hexdigest() # generates an ETag based on the MD5 hash of the JSON string

        if_none_match = request.headers.get('If-None-Match') # gets the 'If-None-Match' header from the request
        if if_none_match == etag: # checks if the client's ETag matches the current ETag
            Logger.debug(f"etag matched for cabinet '{cabinet}', returning 304") # logs a debug message for ETag match
            return '', 304 # returns an empty response with a 304 Not Modified status

        Logger.debug(f"returning inventory json for cabinet '{cabinet}' with etag {etag}") # logs a debug message for returning new data
        response = make_response(inventory_json) # creates a Flask response object with the JSON data
        response.headers['Content-Type'] = 'application/json' # sets the content type header to application/json
        response.headers['ETag'] = etag # sets the ETag header
        response.headers['Cache-Control'] = 'public, max-age=300' # sets cache control headers
        return response # returns the response
    except Exception as e: # catches any exception during API data retrieval
        Logger.error(f"failed to get inventory api data for cabinet '{cabinet}': {e}") # logs an error message
        return jsonify(error="failed to retrieve inventory data"), 500 # returns a JSON error response with a 500 status code

@app.route('/export/csv') # defines the route for exporting inventory to CSV
def export_csv():
    """exports the inventory for a specific cabinet to a CSV file.

    Args:
        cabinet (str, optional): the name of the cabinet to export. Defaults to 'Default'.

    Returns:
        flask.Response: a file response for the CSV download or an error JSON.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    try: # attempts to export to CSV
        return export_manager.export_csv(cabinet) # calls the export_csv method of the export manager
    except Exception as e: # catches any exception during export
        Logger.error(f"export csv failed for cabinet '{cabinet}': {e}") # logs an error message
        return jsonify(error="failed to export csv"), 500 # returns a JSON error response with a 500 status code

@app.route('/export/json') # defines the route for exporting inventory to JSON
def export_json():
    """exports the inventory for a specific cabinet to a JSON file.

    Args:
        cabinet (str, optional): the name of the cabinet to export. Defaults to 'Default'.

    Returns:
        flask.Response: a file response for the JSON download or an error JSON.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    try: # attempts to export to JSON
        return export_manager.export_json(cabinet) # calls the export_json method of the export manager
    except Exception as e: # catches any exception during export
        Logger.error(f"export json failed for cabinet '{cabinet}': {e}") # logs an error message
        return jsonify(error="failed to export json"), 500 # returns a JSON error response with a 500 status code

@app.route('/export/txt') # defines the route for exporting inventory to TXT
def export_txt():
    """exports the inventory for a specific cabinet to a plain text file.

    Args:
        cabinet (str, optional): the name of the cabinet to export. Defaults to 'Default'.

    Returns:
        flask.Response: a file response for the TXT download or an error JSON.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    try: # attempts to export to TXT
        return export_manager.export_txt(cabinet) # calls the export_txt method of the export manager
    except Exception as e: # catches any exception during export
        Logger.error(f"export txt failed for cabinet '{cabinet}': {e}") # logs an error message
        return jsonify(error="failed to export txt"), 500 # returns a JSON error response with a 500 status code

@app.route('/export/excel') # defines the route for exporting inventory to Excel
def export_excel():
    """exports the inventory for a specific cabinet to an Excel (XLSX) file.

    Args:
        cabinet (str, optional): the name of the cabinet to export. Defaults to 'Default'.

    Returns:
        flask.Response: a file response for the Excel download or an error JSON.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    try: # attempts to export to Excel
        return export_manager.export_excel(cabinet) # calls the export_excel method of the export manager
    except Exception as e: # catches any exception during export
        Logger.error(f"export excel failed for cabinet '{cabinet}': {e}") # logs an error message
        return jsonify(error="failed to export excel"), 500 # returns a JSON error response with a 500 status code

@app.route('/export/sheets') # defines the route for exporting inventory to Google Sheets
def export_sheets():
    """handles the request for exporting inventory to Google Sheets (currently not implemented).

    Returns:
        flask.Response: a JSON response indicating that the feature is not implemented.
    """
    try: # attempts to call the export_sheets method
        return export_manager.export_sheets() # calls the export_sheets method of the export manager
    except Exception as e: # catches any exception during the call
        Logger.error(f"export sheets failed: {e}") # logs an error message
        return jsonify(error="failed to export sheets"), 500 # returns a JSON error response with a 500 status code

@app.route('/import/csv', methods=['POST']) # defines the route for importing CSV files
def import_csv():
    """imports inventory data from an uploaded CSV file.

    Returns:
        flask.Response: a JSON response indicating success or failure of the import.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    if 'file' not in request.files: # checks if no file was uploaded
        Logger.warning("no file part in csv import request") # logs a warning
        return jsonify(success=False, error="no file part"), 400 # returns an error response
    file = request.files['file'] # gets the uploaded file
    if file.filename == '': # checks if the filename is empty
        Logger.warning("no selected file for csv import") # logs a warning
        return jsonify(success=False, error="no selected file"), 400 # returns an error response
    if file and file.filename.endswith('.csv'): # checks if a file exists and has a .csv extension
        success = import_manager.import_csv(file, cabinet) # calls the import_csv method of the import manager
        if success: # if import was successful
            return jsonify(success=True) # returns success
        else: # if import failed
            return jsonify(success=False, error="failed to import csv"), 500 # returns an error
    Logger.warning(f"invalid file type for csv import: {file.filename}") # logs a warning for invalid file type
    return jsonify(success=False, error="invalid file type"), 400 # returns an error for invalid file type

@app.route('/import/json', methods=['POST']) # defines the route for importing JSON files
def import_json():
    """imports inventory data from an uploaded JSON file.

    Returns:
        flask.Response: a JSON response indicating success or failure of the import.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    if 'file' not in request.files: # checks if no file was uploaded
        Logger.warning("no file part in json import request") # logs a warning
        return jsonify(success=False, error="no file part"), 400 # returns an error response
    file = request.files['file'] # gets the uploaded file
    if file.filename == '': # checks if the filename is empty
        Logger.warning("no selected file for json import") # logs a warning
        return jsonify(success=False, error="no selected file"), 400 # returns an error response
    if file and file.filename.endswith('.json'): # checks if a file exists and has a .json extension
        success = import_manager.import_json(file, cabinet) # calls the import_json method of the import manager
        if success: # if import was successful
            return jsonify(success=True) # returns success
        else: # if import failed
            return jsonify(success=False, error="failed to import json"), 500 # returns an error
    Logger.warning(f"invalid file type for json import: {file.filename}") # logs a warning for invalid file type
    return jsonify(success=False, error="invalid file type"), 400 # returns an error for invalid file type

@app.route('/import/txt', methods=['POST']) # defines the route for importing TXT files
def import_txt():
    """imports inventory data from an uploaded TXT file.

    Returns:
        flask.Response: a JSON response indicating success or failure of the import.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    if 'file' not in request.files: # checks if no file was uploaded
        Logger.warning("no file part in txt import request") # logs a warning
        return jsonify(success=False, error="no file part"), 400 # returns an error response
    file = request.files['file'] # gets the uploaded file
    if file.filename == '': # checks if the filename is empty
        Logger.warning("no selected file for txt import") # logs a warning
        return jsonify(success=False, error="no selected file"), 400 # returns an error response
    if file and file.filename.endswith('.txt'): # checks if a file exists and has a .txt extension
        success = import_manager.import_txt(file, cabinet) # calls the import_txt method of the import manager
        if success: # if import was successful
            return jsonify(success=True) # returns success
        else: # if import failed
            return jsonify(success=False, error="failed to import txt"), 500 # returns an error
    Logger.warning(f"invalid file type for txt import: {file.filename}") # logs a warning for invalid file type
    return jsonify(success=False, error="invalid file type"), 400 # returns an error for invalid file type

@app.route('/import/excel', methods=['POST']) # defines the route for importing Excel files
def import_excel():
    """imports inventory data from an uploaded Excel file.

    Returns:
        flask.Response: a JSON response indicating success or failure of the import.
    """
    cabinet = request.args.get('cabinet', 'Default') # gets the 'cabinet' query parameter, defaulting to 'Default'
    if 'file' not in request.files: # checks if no file was uploaded
        Logger.warning("no file part in excel import request") # logs a warning
        return jsonify(success=False, error="no file part"), 400 # returns an error response
    file = request.files['file'] # gets the uploaded file
    if file.filename == '': # checks if the filename is empty
        Logger.warning("no selected file for excel import") # logs a warning
        return jsonify(success=False, error="no selected file"), 400 # returns an error response
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')): # checks if a file exists and has an Excel extension
        success = import_manager.import_excel(file, cabinet) # calls the import_excel method of the import manager
        if success: # if import was successful
            return jsonify(success=True) # returns success
        else: # if import failed
            return jsonify(success=False, error="failed to import excel"), 500 # returns an error
    Logger.warning(f"invalid file type for excel import: {file.filename}") # logs a warning for invalid file type
    return jsonify(success=False, error="invalid file type"), 400 # returns an error for invalid file type


def periodic_backup(interval_seconds=300):
    """performs a periodic backup of the entire inventory to a CSV file.

    Args:
        interval_seconds (int, optional): the interval in seconds between backups. Defaults to 300 (5 minutes).
    """
    while True: # runs indefinitely
        try: # handles errors during the backup process
            backup_file = os.path.join(PROJECT_ROOT, 'resources', 'backup.csv') # constructs the full path to the backup CSV file

            cabinets = inventory_manager.get_all_cabinets() # retrieves all cabinet names
            if not cabinets: # checks if no cabinets were found
                Logger.warning("no cabinets found during backup, creating 'default' if none exist") # logs a warning if no cabinets are found

            with open(backup_file, 'w', newline='', encoding='utf-8') as csvfile: # opens the backup file in write mode
                writer = csv.writer(csvfile) # creates a CSV writer object
                writer.writerow(['Cabinet', 'Drawer', 'Name', 'Quantity']) # writes the header row to the backup file

                for cabinet in cabinets: # iterates through each cabinet
                    try: # handles errors for individual cabinet backup
                        inventory = inventory_manager.get_inventory(cabinet) # retrieves the inventory for the current cabinet
                        padded_inventory = pad_inventory(inventory) # pads the inventory

                        for drawer, data in padded_inventory.items(): # iterates through each drawer in the padded inventory
                            writer.writerow([cabinet, drawer, data.get('name', ''), data.get('qty', 0)]) # writes drawer data to the CSV
                    except Exception as e: # catches any exception during a single cabinet backup
                        Logger.error(f"failed to backup cabinet '{cabinet}': {e}") # logs an error for the failed cabinet backup

            Logger.info(f"backed up full inventory to {backup_file}") # logs a success message for the full backup

        except Exception as e: # catches any broader exception during the backup loop
            Logger.error(f"backup failed: {e}") # logs a general backup failure message

        time.sleep(interval_seconds) # pauses execution for the specified interval

if __name__ == '__main__': # checks if the script is being run directly
    backup_thread = threading.Thread(target=periodic_backup, args=(300,), daemon=True) # creates a new thread for periodic backup
    backup_thread.start() # starts the backup thread

    Logger.info("starting flask app on 0.0.0.0:5000") # logs that the Flask app is starting
    app.run(host='0.0.0.0', port=5000, debug=True) # runs the Flask application