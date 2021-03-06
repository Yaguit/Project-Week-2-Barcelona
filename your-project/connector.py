import pymysql
from pathlib import Path
import pandas as pd
import sys
from datetime import datetime

class DBConnector:
    def __init__(self, path):
        credentials = Path(path)
        # check file exists
        if (not credentials.exists()):
            print('ERROR - COULD NOT RECOVER CREDENTIAL FILES')
            sys.exit()
        # open credentials super secret file
        with open(credentials) as f:
            lines = f.read().splitlines()
            f.close()
        # create connector
        self.conn = pymysql.connect(host=lines[0], user=lines[1], password=lines[2], db=lines[3])
        # create cursor
        self.cursor = self.conn.cursor()
        self.insert_sql = 'INSERT INTO {} ({}) VALUES ({})'

    def insert_values(self, table, columns, values, row):
        try:
            self.cursor.execute(self.insert_sql.format(table, columns, values), row)
            self.conn.commit()
        except pymysql.Error as e:
            if (str(e).__contains__('Duplicate')):
                print(f'DUPLICATED VALUE --> {row}')
            else:
                print(f'ERROR - could not insert querie {self.insert_sql.format(table_name, column_names, values)} with params {row}')
            self.conn.rollback()
    
    def execute_query(self, sql):
        return pd.read_sql(sql, self.conn)
    
    def close_connection(self):
        self.cursor.close()
        self.conn.close()


def recover_integer(val):
    try:
        new_val = int(val)
    except:
        new_val = -1
    return new_val

def recover_date(val):
    try:
        generated = datetime.strptime(val, '%d/%m/%Y %H:%M')
    except:
        print('ERROR - could not parse date: ', val)
        generated = datetime.now()
    return generated.strftime('%Y-%m-%d %H:%M:%S')





# create the connector
db_conn = DBConnector(Path('./Project-Week-2-Barcelona/connection/credentials.txt'))
# recover file to insert
########################
# STATION ##############
########################
data_folder = Path('./Project-Week-2-Barcelona/datasets/2.-Urban-Environment/air-stations-nov-2017.csv')
station_df = pd.read_csv(data_folder)
print('\nimported data -->\n', station_df)
# setting values to create the inserts
table_name = 'Station'
column_names = 'name, lat, lng'
values = '%s,%s,%s'

for i,row in station_df.iterrows():
    db_conn.insert_values(table_name, column_names, values, [row[0], row[1], row[2]])


########################
# REGISTRY #############
########################
data_folder = Path('./Project-Week-2-Barcelona/datasets/2.-Urban-Environment/air-quality-nov-2017.csv')
registry_df = pd.read_csv(data_folder)
print('\nimported data -->\n', registry_df)
# setting values to create the inserts
table_name = 'Registry'
column_names = 'no2_Val, o3_Val, pm_val, date_generate, station_ID'
values = '%s,%s,%s,%s,%s'

# get station IDs
stations = db_conn.execute_query('SELECT ID as station_ID, name FROM Station')

for i,row in registry_df.iterrows():
    station = stations.query(f'name == \'{row["Station"].strip()}\'')
    if (station.size == 0):
        print('no station found with name ',row["Station"])
        # print('\n\nWARNING - row not saved \n',row)
        continue
    station_ID = recover_integer(station.station_ID)
    if (station_ID == -1):
        print('no station saved with name ',row["Station"])
        continue
    no2_value = recover_integer(row['NO2 Value'])
    o3_value = recover_integer(row['O3 Value'])
    pm10_value = recover_integer(row['PM10 Value'])
    date_generated = recover_date(str(row.Generated))
    row_values = [no2_value, o3_value, pm10_value, date_generated, int(station_ID)]
    db_conn.insert_values(table_name, column_names, values, row_values)

# close connections
db_conn.close_connection()