"""API to receive requests for access to the Temperature display devices"""

from flask import request, g, redirect, url_for, \
    render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.takeabeltof.date_utils import local_datetime_now
from shotglass2.users.admin import login_required, table_access_required
from temp_center.models import Device, Sensor, Reading

from datetime import datetime, timedelta

mod = Blueprint('api', __name__, template_folder='templates/',
                url_prefix='/api')


@mod.route('/<path:path>', methods=['GET'])
@mod.route('/<path:path>/', methods=['GET'])
@mod.route('/', methods=['GET'])
def add_reading(path:str=None):
    """Recode a reading from a sensor sent here
    
    The values are sent by positional data included in the path separated by slashes.
    The format is:
        <sensor_id>/
        <temperature (corrected as displayed on device)>/
        <raw_temperature (uncorrected temp)
        <scale (F or C)>/
    
    So it would look something like: '/1/78.2/74.2/F/'

    """
    result = ""
    error_list = []
    rec = {}

    # import pdb;pdb.set_trace()

    if not path:
        return 'No path'

    path = path.strip()
    path_list = path.split("/")
    print(path_list)

    if len(path_list) == 5:
        # has all elements
        rec['sensor_id'] = cleanRecordID(path_list[1].strip())  # path_list[0] is the method name
        rec['temperature'] = path_list[2].strip()
        rec['raw_temperature'] = path_list[3].strip()
        rec['scale'] = path_list[4].strip().upper()
        rec['reading_time'] = local_datetime_now()
    else:
        #Not a valid request, stop right here
        return "Too Short"

    #validate each item
    if rec['sensor_id'] and Sensor(g.db).get(rec['sensor_id']):
        pass # sensor ID exists
    else:
        error_list.append("Invalid Sensor ID")

    try:
        rec['temperature'] = float(rec['temperature'])
    except ValueError:
        error_list.append("Temperature invalid")
    except:
        error_list.append("Bad temperature data")

    if len(rec['scale']) < 1 or rec['scale'][0] not in ("F","C"):
        error_list.append("Scale invalid")

    if not error_list:
        # Record the reading
        new_rec = Reading(g.db).new()
        new_rec.update(rec,True)

        # remove a bunch of old readings
        end_date = (local_datetime_now() - timedelta(days=4)).date()
        sql = "delete from reading where date(reading_time) < '{}'".format(end_date)
        test = Reading(g.db).query(sql)

        Reading(g.db).commit()

        result = "OK"
    else:
        result = ','.join(error_list)

    return result
