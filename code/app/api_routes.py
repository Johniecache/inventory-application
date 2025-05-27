from flask import Blueprint, jsonify, request, Response
from app.inventory_manager import InventoryManager
from Logger import Logger

api = Blueprint('api', __name__) # creates a Flask Blueprint named 'api'
inventory = InventoryManager() # creates an instance of the InventoryManager class

def validate_int(val, name):
    """validates if a given value can be converted to an integer.

    Args:
        val (any): the value to be validated.
        name (str): the name of the value, used for error messages.

    Raises:
        ValueError: if the value cannot be converted to an integer.

    Returns:
        int: the integer representation of the validated value.
    """
    try: # handles errors
        return int(val) # attempts to convert the value to an integer and returns it
    except (ValueError, TypeError): # catches ValueError or TypeError if conversion fails
        raise ValueError(f"invalid {name}: {val}") # raises a ValueError with a descriptive message

@api.route('/api/cabinets', methods=['GET']) # defines a route for GET requests to /api/cabinets
def get_cabinets():
    """retrieves all cabinet names from the inventory.

    Args:
        none

    Returns:
        json: a JSON response containing the list of cabinet names.
        Response: an error response if the operation fails.
    """
    try: # handles errors
        cabinets = inventory.get_all_cabinets() # retrieves all cabinet names using the inventory manager
        Logger.info("fetched all cabinet names") # logs an informational message
        return jsonify({"cabinets": cabinets}) # returns a JSON response with the cabinet names
    except Exception as e: # catches any exception that occurs
        Logger.error(f"failed to fetch cabinets: {e}") # logs an error message with the exception details
        return Response("internal server error", status=500) # returns a 500 Internal Server Error response

@api.route('/api/cabinets/<cabinet_name>/drawers', methods=['GET']) # defines a route for GET requests to /api/cabinets/<cabinet_name>/drawers
def get_drawers(cabinet_name):
    """retrieves all drawers for a specific cabinet.

    Args:
        cabinet_name (str): the name of the cabinet.

    Returns:
        json: a JSON response containing the drawers for the specified cabinet.
        Response: an error response if the operation fails.
    """
    try: # handles errors
        drawers = inventory.get_inventory(cabinet_name) # retrieves the inventory for the specified cabinet
        Logger.info(f"fetched drawers for cabinet '{cabinet_name}'") # logs an informational message
        return jsonify(drawers) # returns a JSON response with the drawers
    except Exception as e: # catches any exception that occurs
        Logger.error(f"failed to fetch drawers for cabinet '{cabinet_name}': {e}") # logs an error message
        return Response("internal server error", status=500) # returns a 500 Internal Server Error response

@api.route('/api/cabinets/<cabinet_name>/drawers', methods=['POST']) # defines a route for POST requests to /api/cabinets/<cabinet_name>/drawers
def add_drawer(cabinet_name):
    """adds a new drawer to a specific cabinet.

    Args:
        cabinet_name (str): the name of the cabinet to which the drawer will be added.

    Returns:
        json: a JSON response indicating success.
        Response: an error response if the operation fails due to missing data, validation issues, or other exceptions.
    """
    try: # handles errors
        data = request.json # gets the JSON data from the request body
        row = data.get("row") # extracts the 'row' value from the data
        col = data.get("col") # extracts the 'col' value from the data
        name = data.get("name", "") # extracts the 'name' value, defaults to an empty string
        quantity = data.get("quantity", 0) # extracts the 'quantity' value, defaults to 0

        if row is None or col is None: # checks if 'row' or 'col' are missing
            return Response("missing 'row' or 'col' in request", status=400) # returns a 400 Bad Request if data is missing

        row = validate_int(row, "row") # validates and converts 'row' to an integer
        col = validate_int(col, "col") # validates and converts 'col' to an integer
        quantity = validate_int(quantity, "quantity") # validates and converts 'quantity' to an integer

        inventory.update_drawer(f"{chr(row)}{col}", name, quantity) # updates the drawer with the provided information
        Logger.info(f"added drawer {row}_{col} to cabinet '{cabinet_name}'") # logs an informational message
        return jsonify({"success": True}) # returns a JSON response indicating success
    except ValueError as ve: # catches ValueError specifically for validation issues
        Logger.warning(f"validation error adding drawer: {ve}") # logs a warning message
        return Response(str(ve), status=400) # returns a 400 Bad Request with the validation error message
    except Exception as e: # catches any other exception
        Logger.error(f"failed to add drawer: {e}") # logs an error message
        return Response("internal server error", status=500) # returns a 500 Internal Server Error response

@api.route('/api/cabinets/<cabinet_name>/drawers/<int:row>_<int:col>', methods=['PUT']) # defines a route for PUT requests to update a specific drawer
def update_drawer(cabinet_name, row, col):
    """updates an existing drawer in a specific cabinet.

    Args:
        cabinet_name (str): the name of the cabinet where the drawer is located.
        row (int): the row identifier of the drawer.
        col (int): the column identifier of the drawer.

    Returns:
        json: a JSON response indicating success.
        Response: an error response if the operation fails due to validation issues or other exceptions.
    """
    try: # handles errors
        data = request.json or {} # gets the JSON data from the request, defaults to an empty dictionary
        name = data.get("name", "") # extracts the 'name' value, defaults to an empty string
        quantity = data.get("quantity", 0) # extracts the 'quantity' value, defaults to 0
        quantity = validate_int(quantity, "quantity") # validates and converts 'quantity' to an integer

        inventory.update_drawer(f"{chr(row)}{col}", name, quantity) # updates the drawer with the provided information
        Logger.info(f"updated drawer {row}_{col} in cabinet '{cabinet_name}'") # logs an informational message
        return jsonify({"success": True}) # returns a JSON response indicating success
    except ValueError as ve: # catches ValueError specifically for validation issues
        Logger.warning(f"validation error updating drawer: {ve}") # logs a warning message
        return Response(str(ve), status=400) # returns a 400 Bad Request with the validation error message
    except Exception as e: # catches any other exception
        Logger.error(f"failed to update drawer: {e}") # logs an error message
        return Response("internal server error", status=500) # returns a 500 Internal Server Error response

@api.route('/api/cabinets/<cabinet_name>/drawers/<int:row>_<int:col>', methods=['DELETE']) # defines a route for DELETE requests to remove a specific drawer
def delete_drawer(cabinet_name, row, col):
    """deletes a drawer from a specific cabinet by setting its name and quantity to default values.

    Args:
        cabinet_name (str): the name of the cabinet from which the drawer will be deleted.
        row (int): the row identifier of the drawer.
        col (int): the column identifier of the drawer.

    Returns:
        json: a JSON response indicating success.
        Response: an error response if the operation fails.
    """
    try: # handles errors
        inventory.update_drawer(f"{chr(row)}{col}", "", 0) # effectively "deletes" the drawer by setting its name to empty and quantity to 0
        Logger.info(f"deleted drawer {row}_{col} from cabinet '{cabinet_name}'") # logs an informational message
        return jsonify({"success": True}) # returns a JSON response indicating success
    except Exception as e: # catches any exception
        Logger.error(f"failed to delete drawer: {e}") # logs an error message
        return Response("internal server error", status=500) # returns a 500 Internal Server Error response