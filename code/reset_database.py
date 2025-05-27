import sqlite3
import os
from app.Logger import Logger

DB_PATH = os.path.join(os.path.dirname(__file__), 'resources', 'database.db') # get the path to the database

conn = sqlite3.connect(DB_PATH) # establish connection to database via sqlite3
c = conn.cursor() # initialize cursor to execute sql commands

c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drawers'") # check if drawers table exists
table_exists = c.fetchone() is not None # get table if it does exist

if not table_exists: # if the table doesnt exist
    c.execute(''' 
    CREATE TABLE drawers (
        id TEXT PRIMARY KEY,
        row TEXT,
        column TEXT,
        name TEXT,
        qty INTEGER,
        cabinet TEXT
    )
    ''') # create new table with these identifiers
    Logger.info("Table 'drawers' created.") # log info
else: # if table does exist
    c.execute("PRAGMA table_info(drawers)") # create table info with drawers
    columns = {col[1]: col[2] for col in c.fetchall()} # fetch the columns for each column

    if columns.get('id') == 'INTEGER': # if id is an INTEGER type
        Logger.info("Changing 'id' column from INTEGER to TEXT...") # log that its being changed
        c.execute("ALTER TABLE drawers RENAME TO drawers_old") # rename to old reawers
        c.execute('''
        CREATE TABLE drawers (
            id TEXT PRIMARY KEY,
            row TEXT,
            column TEXT,
            name TEXT,
            qty INTEGER,
            cabinet TEXT
        )
        ''') # change id to text instead of integer
        c.execute('''
        INSERT INTO drawers (id, row, column, name, qty, cabinet)
        SELECT id, row, column, name, qty, cabinet FROM drawers_old
        ''') # change it in drawers
        c.execute("DROP TABLE drawers_old") # update the dropdown bar of old drawers
        Logger.info("Column 'id' converted to TEXT") # confirm that id has been converted
    elif 'cabinet' not in columns: # id is an integer but cabinet is not in the database
        Logger.info("Column 'cabinet' missing, migrating table schema...") # log that cabinet is being migrated into existing database
        c.execute("ALTER TABLE drawers RENAME TO drawers_old") # alter current table
        c.execute('''
        CREATE TABLE drawers (
            id TEXT PRIMARY KEY,
            row TEXT,
            column TEXT,
            name TEXT,
            qty INTEGER,
            cabinet TEXT
        )
        ''') # add cabinets as text in fields
        c.execute('''
        INSERT INTO drawers (id, row, column, name, qty, cabinet)
        SELECT id, row, column, name, qty, 'Default' FROM drawers_old
        ''') # insert teh drawers into the table
        c.execute("DROP TABLE drawers_old") # put old drawers into new ones
        Logger.info("Table schema migrated with new 'cabinet' column.") # log that cabinet has been merged together
    else:
        Logger.info("Table and column 'cabinet' already exists.") # if table exists with cabinets then log that it does

conn.commit() # commit these changes
conn.close() # close connection to database
Logger.info("Database setup complete.") # log conifmation
