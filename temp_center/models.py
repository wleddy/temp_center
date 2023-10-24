from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
        
class Calibration(SqliteTable):
    """Represents a single reading from a sensor"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'calibration'
        self.order_by_col = 'sensor_id,raw_temperature'
        self.defaults = {}
        
    def create_table(self):
        """Define and create a table"""
        
        sql = """
            'raw_temperature' NUMBER,
            'observed_temperature' NUMBER,
            'sensor_id' INTEGER,
            FOREIGN KEY (sensor_id) REFERENCES sensor(id) ON DELETE CASCADE """
        super().create_table(sql)


class Device(SqliteTable):
    """Represents the physical temperature display device"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'device'
        self.order_by_col = 'lower(name)'
        self.defaults = {}
        
    def create_table(self):
        """Define and create a table"""
        
        sql = """
            'name' TEXT UNIQUE NOT NULL,
            'description' TEXT """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        """
    
        column_list = [
        # {'name':'expires','definition':'DATETIME',},
        ]
    
        return column_list

class Sensor(SqliteTable):
    """Represents the sensors that are connected to a device"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'sensor'
        self.order_by_col = 'sort_order,lower(name)'
        self.defaults = {}
        
    def create_table(self):
        """Define and create a table"""
        
        sql = """
            'name' TEXT NOT NULL,
            'device_id' INTEGER,
            FOREIGN KEY (device_id) REFERENCES device(id) ON DELETE CASCADE """
        
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        """
    
        column_list = [
        {'name':'sort_order','definition':'NUMBER',},
        {'name':'scale','definition':'TEXT',},
        ]
    
        return column_list

class Reading(SqliteTable):
    """Represents a single reading from a sensor"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'reading'
        self.order_by_col = 'reading_time DESC'
        self.defaults = {}
        
    def create_table(self):
        """Define and create a table"""
        
        sql = """
            'temperature' NUMBER,
            'raw_temperature' NUMBER,
            'scale' TEXT,
            'reading_time' DATETIME,
            'sensor_id' INTEGER,
            FOREIGN KEY (sensor_id) REFERENCES sensor(id) ON DELETE CASCADE """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        """
    
        column_list = [
        # {'name':'expires','definition':'DATETIME',},
        ]
    
        return column_list


def init_db(db):
    """Create Tables."""
    l = globals().copy()
    for n,o in l.items():
        if type(o) == type and \
            issubclass(o,SqliteTable) and \
            o != SqliteTable:
            
            o(db).init_table()
            
            
