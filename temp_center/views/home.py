from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from temp_center.models import Sensor, Device, Reading

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
    select reading.id, round(temperature,1) as temperature, scale, device.name as device_name, sensor.name as sensor_name
    from reading
    join sensor on sensor.id = reading.sensor_id
    join device on device.id = sensor.device_id
    where device.id = {device_id} and sensor.id = {sensor_id}
    order by reading.id DESC
    limit 1
    """

    data = []
    sensors = []
    # import pdb;pdb.set_trace()
    devices = Device(g.db).select(order_by="name")
    print("Devices: ", devices)
    if devices:
        for device in devices:
            sensors = Sensor(g.db).select(where="device_id = {}".format(device.id),order_by="name DESC")
            print("Sensors:",sensors)
            if sensors:
                for sensor in sensors:
                    data.append(Reading(g.db).query(sql.format(device_id = device.id, sensor_id = sensor.id))[0])

    print(data)


    return render_template("home/home.html",data=data)