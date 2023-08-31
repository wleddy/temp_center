"""API to receive requests for access to the Temperature display devices"""

from flask import request, g, redirect, url_for, \
    render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.date_utils import make_tz_aware
from shotglass2.users.admin import login_required, table_access_required
from temp_center.models import Device, Sensor, Reading

from datetime import datetime

mod = Blueprint('api', __name__, template_folder='templates/',
                url_prefix='/')


@mod.route('/<path:path>', methods=['GET'])
@mod.route('/<path:path>/', methods=['GET'])
@mod.route('/', methods=['GET'])
def add_reading(path:str=None):
    """Recode a reading from a sensor sent here
    
    The values are sent by positional data included in the path separated by slashes.
    The format is:
        <sensor_id>/
        <temperature (as displayed on device)>/
        <scale (F or C)>/
        <time (in seconds since unix epoc)>/
    
    So it would look something like: '/1/78.2/F/23423222/'

    """
    result = ""
    error_list = []
    rec = {}

    import pdb;pdb.set_trace()

    path = path.strip()
    path_list = path.split("/")
    print(path_list)

    if len(path_list) == 5:
        # has all elements
        rec['sensor_id'] = cleanRecordID(path_list[1].strip())  # path_list[0] is the method name
        rec['temperature'] = path_list[2].strip()
        rec['scale'] = path_list[3].strip().upper()
        rec['reading_time'] = path_list[4].strip()
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

    if not rec['reading_time']:
        error_list.append("Missing time")
    else:
        # convert to Datetime
        try:
            rec['reading_time'] = float(rec['reading_time'])
            rec['reading_time'] = make_tz_aware(datetime.fromtimestamp(rec['reading_time']))
        except:
            error_list.append("Invalid reading time")
    
    if not error_list:
        # Record the reading
        new_rec = Reading(g.db).new()
        new_rec.update(rec,True)
        new_rec.commit()

        result = "OK"
    else:
        result = ','.join(error_list)

    return result
