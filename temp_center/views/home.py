from enphase import enphase
from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from temp_center.models import Sensor, Device, Reading, Production
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
    
    # get the solor production numbers
    update_production_database()
    query_date = str(local_datetime_now() - timedelta(days=6))[0:10]
    # remove records older than 7 days
    prod_recs = Production(g.db).query(f"delete from production where production_date < '{query_date}'")

   
    sql = f"""Select production, 
    production_date,
    "" as day_letter
    from production
    order by production_date
    limit 7
    """
    prod_recs = Production(g.db).query(sql)
    # limit selection to 7 days
    if prod_recs:
        for prod_rec in prod_recs:
            prod_rec.day_letter = short_day_and_date_string(getDatetimeFromString(prod_rec.production_date))[0:1]
            try:
                prod_rec.production = round(float(prod_rec.production)/1000,0) #convert to kWh
            except:
                prod_rec.production = -1.0

        # # for testing... load a range of values
        # kwh = 3
        # for x in range(len(prod_recs)):
        #     prod_recs[x].production = kwh
        #     kwh += 18/7 
        
    return render_template("home/home.html",
                           data=data,history=history, 
                           production=prod_recs,
                           )


def update_production_database() -> None:
    """ Get current solar production data
    
    Query the local Enphase Gateway to get the latest production data, update
    the production table.

    It looks like the gateway does not consider that a new day has started until
    at least some electrons have been shifted and it keeps reporting the total from the
    previous day. So... If the date has changed from the most recent record, and the 
    production reported is the same as the previous day, save the record with 0 production
    until the reported production is different from the previous day.
    
    Args: None
    
    Returns:  None
    
    Raises: None
    """

    current_data = enphase.get_local_production()
    prod = Production(g.db)

    today = str(local_datetime_now())[0:10] #Date only
    prev_rec = prod.query_one(f"select * from production where production_date < '{today}' order by production_date DESC")
    # Select or create a production record
    rec = prod.select_one(where=f"production_date = '{today}'")
    if not rec:
        rec = prod.new()
        rec.production_date = today
        rec.production = 0.0
    watthours = current_data.get("wattHoursToday")
    if watthours:
        if not prev_rec:
            rec.production = watthours # First record ever
        elif prev_rec.production == watthours and rec.production == 0.0:
            pass # gateway is still returning yesterday's production
        else:
            rec.production = watthours

    rec.save()
    rec.commit()


def temp_history() -> list:
    """ Return a list of DataRow objects of the 
    min and max temps for the last few days
    
    Args: None
    
    Returns:  list of DataRows
    
    Raises: None
    """
    # import pdb; pdb.set_trace()

    query_date = (local_datetime_now() - timedelta(days=6))

    sql = """select 
    substr(reading_time,1,10) as reading_date, 
    round(max(temperature),0) as max, 
    round(min(temperature),0) as min, 
    round((select max(temperature) from reading where reading.sensor_id = sensor.id and reading_time >= date('{query_date}','localtime') order by reading_time DESC limit 7),0) as weekly_max,
    round((select min(temperature) from reading where reading.sensor_id = sensor.id and reading_time >= date('{query_date}','localtime') order by reading_time DESC limit 7),0) as weekly_min,
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
            row.daily_range =  round(normalize_range(row.max,row.scale) - normalize_range(row.min,row.scale),0)
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

