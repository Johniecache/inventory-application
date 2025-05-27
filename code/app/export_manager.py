import io
import csv
import json
import pandas as pd
from utilities import pad_inventory
from flask import send_file, Response, jsonify
from Logger import Logger

class ExportManager:
    """handles the process of exporting the data to a specific file type.
    """
    def __init__(self, inventory_manager, pad_func):
        """constructor for class.

        Args:
            inventory_manager (class): instance of inventory manager.
            pad_func (class): instance of pad function.
        """
        self.inventory_manager = inventory_manager # initializes the inventory manager instance
        self.pad_inventory = pad_func # initializes the pad function

    def export_csv(self, cabinet):
        """exports the inventory data for a given cabinet to a CSV file.

        Args:
            cabinet (str): the name of the cabinet whose inventory is to be exported.

        Returns:
            flask.Response: a Flask response containing the CSV file as an attachment.
            flask.Response: an error response if the export fails.
        """
        try: # handles errors during the export process
            inventory = self.pad_inventory(self.inventory_manager.get_inventory(cabinet)) # gets the inventory for the specified cabinet and pads it
            output = io.StringIO() # creates an in-memory text buffer
            writer = csv.writer(output) # creates a CSV writer object for the buffer
            writer.writerow(['ID', 'Name', 'Quantity']) # writes the header row to the CSV
            for key, value in inventory.items(): # iterates through each item in the inventory
                writer.writerow([key, value.get('name', ''), value.get('qty', 0)]) # writes each item's ID, name, and quantity to the CSV
            output.seek(0) # moves the buffer's cursor to the beginning
            Logger.info(f"csv export successful for cabinet '{cabinet}'") # logs a success message
            return send_file( # returns the CSV file as a downloadable attachment
                io.BytesIO(output.getvalue().encode()), # converts the string buffer content to bytes
                mimetype='text/csv', # sets the MIME type for CSV
                as_attachment=True, # specifies that the file should be downloaded as an attachment
                download_name='inventory.csv' # sets the default download filename
            )
        except Exception as e: # catches any exception that occurs during export
            Logger.error(f"csv export failed for cabinet '{cabinet}': {e}") # logs an error message with the exception details
            return Response("failed to export csv", status=500) # returns a 500 Internal Server Error response

    def export_json(self, cabinet):
        """exports the inventory data for a given cabinet to a JSON file.

        Args:
            cabinet (str): the name of the cabinet whose inventory is to be exported.

        Returns:
            flask.Response: a Flask response containing the JSON file as an attachment.
            flask.Response: an error response if the export fails.
        """
        try: # handles errors during the export process
            inventory = self.pad_inventory(self.inventory_manager.get_inventory(cabinet)) # gets the inventory for the specified cabinet and pads it
            Logger.info(f"json export successful for cabinet '{cabinet}'") # logs a success message
            return Response( # returns the JSON data as a downloadable attachment
                json.dumps(inventory, indent=2), # converts the inventory dictionary to a JSON string with 2-space indentation
                mimetype='application/json', # sets the MIME type for JSON
                headers={"Content-Disposition": "attachment;filename=inventory.json"} # sets the header to suggest a download filename
            )
        except Exception as e: # catches any exception that occurs during export
            Logger.error(f"json export failed for cabinet '{cabinet}': {e}") # logs an error message with the exception details
            return Response("failed to export json", status=500) # returns a 500 Internal Server Error response

    def export_txt(self, cabinet):
        """exports the inventory data for a given cabinet to a plain text file.

        Args:
            cabinet (str): the name of the cabinet whose inventory is to be exported.

        Returns:
            flask.Response: a Flask response containing the text file as an attachment.
            flask.Response: an error response if the export fails.
        """
        try: # handles errors during the export process
            inventory = self.pad_inventory(self.inventory_manager.get_inventory(cabinet)) # gets the inventory for the specified cabinet and pads it
            lines = [f"{key}: {val.get('name', '')} ({val.get('qty', 0)})" for key, val in inventory.items()] # creates a list of formatted strings for each inventory item
            Logger.info(f"txt export successful for cabinet '{cabinet}'") # logs a success message
            return Response( # returns the text data as a downloadable attachment
                "\n".join(lines), # joins the list of lines into a single string separated by newlines
                mimetype='text/plain', # sets the MIME type for plain text
                headers={"Content-Disposition": "attachment;filename=inventory.txt"} # sets the header to suggest a download filename
            )
        except Exception as e: # catches any exception that occurs during export
            Logger.error(f"txt export failed for cabinet '{cabinet}': {e}") # logs an error message with the exception details
            return Response("failed to export txt", status=500) # returns a 500 Internal Server Error response

    def export_excel(self, cabinet):
        """exports the inventory data for a given cabinet to an Excel (XLSX) file.

        Args:
            cabinet (str): the name of the cabinet whose inventory is to be exported.

        Returns:
            flask.Response: a Flask response containing the Excel file as an attachment.
            flask.Response: an error response if the export fails.
        """
        try: # handles errors during the export process
            inventory = self.pad_inventory(self.inventory_manager.get_inventory(cabinet)) # gets the inventory for the specified cabinet and pads it
            df = pd.DataFrame( # creates a pandas DataFrame from the inventory data
                [(k, v.get('name', ''), v.get('qty', 0)) for k, v in inventory.items()], # list comprehension to format data for DataFrame
                columns=['ID', 'Name', 'Quantity'] # sets the column names for the DataFrame
            )
            output = io.BytesIO() # creates an in-memory binary buffer
            with pd.ExcelWriter(output, engine='openpyxl') as writer: # creates an Excel writer object using openpyxl engine
                df.to_excel(writer, index=False, sheet_name='Inventory') # writes the DataFrame to the Excel writer, without index and with a sheet name
            output.seek(0) # moves the buffer's cursor to the beginning
            Logger.info(f"excel export successful for cabinet '{cabinet}'") # logs a success message
            return send_file( # returns the Excel file as a downloadable attachment
                output, # the in-memory binary buffer containing the Excel data
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # sets the MIME type for XLSX
                as_attachment=True, # specifies that the file should be downloaded as an attachment
                download_name='inventory.xlsx' # sets the default download filename
            )
        except Exception as e: # catches any exception that occurs during export
            Logger.error(f"excel export failed for cabinet '{cabinet}': {e}") # logs an error message with the exception details
            return Response("failed to export excel", status=500) # returns a 500 Internal Server Error response

    def export_sheets(self):
        """indicates that Google Sheets export functionality is not yet implemented.

        Returns:
            flask.Response: a JSON response indicating the status of the feature.
        """
        Logger.warning("google sheets export not yet implemented") # logs a warning message
        return jsonify({"status": "google sheets export not yet implemented"}), 501 # returns a JSON response with a 501 Not Implemented status
