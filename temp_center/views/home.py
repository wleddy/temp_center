from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from temp_center.models import Sensor, Device, Reading
from datetime import datetime

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
    select reading.id, round(temperature,1) as temperature, scale, 
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


    return render_template("home/home.html",data=data)
