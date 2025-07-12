from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from temp_center.models import Sensor, Device, Reading
from datetime import datetime, timedelta
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString
from shotglass2.takeabeltof.jinja_filters import short_day_and_date_string

mod = Blueprint('home',__name__, template_folder='templates/', url_prefix='')


def setExits():
    # g.listURL = url_for('.display')
    # g.editURL = url_for('.edit')
    # g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'The Gizmo'


@mod.route('/', methods=['GET',])
def home():
    """The home page..."""
    setExits()

    sql = """
    select reading.id, round(temperature,1) as temperature, reading.scale, 
        device.name as device_name, sensor.name as sensor_name, 
        (select max(reading_time) from reading) as reading_time,
        (select round(max(temperature),0) from reading where sensor_id = {sensor_id} 
            and date(reading_time,'localtime') = '{today}') as max_temp,
        (select round(min(temperature),0) from reading where sensor_id = {sensor_id} 
            and date(reading_time, 'localtime') = '{today}') as min_temp
    from reading
    join sensor on sensor.id = reading.sensor_id
    join device on device.id = sensor.device_id
    where sensor.id = {sensor_id}
    order by reading.reading_time DESC
    limit 1
    """

    data = []
    sensors = []
    today = datetime.now().strftime('%Y-%m-%d')
    # import pdb;pdb.set_trace()
    devices = Device(g.db).select(order_by="name")
    if devices:
        for device in devices:
            sensors = Sensor(g.db).select(where="device_id = {}".format(device.id),order_by="name DESC")
            if sensors:
                for sensor in sensors:
                    readings = Reading(g.db).query(sql.format(sensor_id = sensor.id,today=today))
                    if readings:
                        data.append(readings[0])
        
        history = temp_history() # About a weeks worth of data

    return render_template("home/home.html",data=data,history=history)


def temp_history() -> list:
    """ Return a list of DataRow objects of the 
    min and max temps for the last few days
    
    Args: None
    
    Returns:  list of DataRows
    
    Raises: None
    """
    # import pdb; pdb.set_trace()

    query_date = (local_datetime_now() - timedelta(days=7))

    sql = """select 
    substr(reading_time,1,10) as reading_date, 
    max(temperature) as max, 
    min(temperature) as min, 
    (select max(temperature) from reading where reading.sensor_id = sensor.id order by reading_time DESC limit 7) as weekly_max,
    (select min(temperature) from reading where reading.sensor_id = sensor.id order by reading_time DESC limit 7) as weekly_min,
    reading.scale as scale,
    0 as daily_range,
    0 as weekly_range,
    "" as day_letter, 
    sensor.name 
    from reading 
    join sensor on sensor_id = sensor.id 
    where reading_time >= date('{query_date}','localtime')
    group by sensor.id, substr(reading_time,1,10)
    order by sensor.name DESC, reading_date
    limit 14""".format(query_date=query_date)
    
    rows = Reading(g.db).query(sql)

    if rows:
        # calulate the temp ranges
        for row in rows:
            row.daily_range = round(normalize_range(row.max,row.scale) - normalize_range(row.min,row.scale),0)
            row.weekly_range = round(normalize_range(row.weekly_max,row.scale) - normalize_range(row.weekly_min,row.scale),0)
            # represent the day in the chart as the first letter of the day
            row.day_letter = short_day_and_date_string(getDatetimeFromString(row.reading_date))[0:1]
            
    return rows


def normalize_range(val,scale):
    """ convert negative temps to whole numbers
    
    If the temp is less than zero convert it to the number
    of degrees from zero
    
    Args: val: float; the number to convert
          scale: str; C or F
    
    Returns:  float
    
    Raises: None
    """

    if val < 0:
        val = abs(val)
        if scale.upper() == 'F':
            val += 32

    return val

