def pad_inventory(inventory):
    """all drawer maker

    Args:
        inventory (String): identifiers for specific drawers

    Returns:
        inventory: all values for a unique drawer
    """
    for row in ['A', 'B', 'C', 'D']: # small drawers
        for col in range(1, 10): # loop through row/column
            key = f"{row}{col}" # set a key for each one
            if key not in inventory: # if there isnt already a key of the drawer
                inventory[key] = {"name": "", "qty": 0} # create one with default values
    for row in ['E', 'F', 'G']: # large drawers
        for col in range(1, 5): # loop through row/column
            key = f"{row}{col}" # unique key for each drawer
            if key not in inventory: # if it doesn't exist
                inventory[key] = {"name": "", "qty": 0} # create a default one
    return inventory # return these drawers

def generate_all_drawer_keys():
    """makes all the drawer unique key value

    Returns:
        keys: row/column for each drawer
    """
    keys = [] # initilize keys
    for row in ['A', 'B', 'C', 'D']: # loop through each unique row
        keys.extend(f"{row}{col}" for col in range(1, 10)) # loop through columns
    for row in ['E', 'F', 'G']: # loop through each unique row
        keys.extend(f"{row}{col}" for col in range(1, 5)) # loop through columns
    return keys # return keys
