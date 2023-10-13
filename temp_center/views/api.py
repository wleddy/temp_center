"""API to receive requests for access to the Temperature display devices"""

from flask import g, redirect, url_for, send_file, abort, \
    render_template, Blueprint, request

from shotglass2.shotglass import make_path
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.takeabeltof.date_utils import local_datetime_now
from shotglass2.users.admin import login_required, table_access_required
from temp_center.models import Device, Sensor, Reading

from datetime import datetime, timedelta
import os
import json

mod = Blueprint('api', __name__, template_folder='templates/',
                url_prefix='/api')


@mod.route('/add_reading/<path:path>', methods=['GET'])
@mod.route('/add_reading/<path:path>/', methods=['GET'])
@mod.route('/add_reading', methods=['GET'])
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

    if len(path_list) == 4:
        # has all elements
        rec['sensor_id'] = cleanRecordID(path_list[0].strip())  # path_list[0] is the method name
        rec['temperature'] = path_list[1].strip()
        rec['raw_temperature'] = path_list[2].strip()
        rec['scale'] = path_list[3].strip().upper()
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
        end_date = (local_datetime_now() - timedelta(days=1))
        sql = "delete from reading where date(reading_time,'localtime') < date('{}','localtime')".format(end_date)
        test = Reading(g.db).query(sql)

        Reading(g.db).commit()

        result = "OK"
    else:
        result = ','.join(error_list)

    return result

@mod.route('/get_file/<path:path>', methods=['GET'])
def get_file(path):
    """Return a file from the app directory of
    the weather_station repo cloned to this site
    """
    # import pdb;pdb.set_trace()

    if not path or not isinstance(path,str):
        return abort(404)
    
    path = os.path.join('weather_station/app/',path)

    if not os.path.isfile(path):
        abort(404)
    
    try:
        return send_file(path, as_attachment=True, max_age=0,)
    except:
        return abort(404)


@mod.route('/log', methods=['GET','POST'])
@mod.route('/log/', methods=['GET','POST'])
def log():
    """Record or get the remote log from the weather station"""
    
    # import pdb;pdb.set_trace()
    
    path = 'instance/remote_logs/'
    data = None
    
    def make_file(filename):
        # create the file if needed
        if not os.path.exists(filename):
            if make_path(filename):
                with open(filename,'w') as f:
                    pass
                
                
    def get_log_name(filename,device_name,number):
        return os.path.join(os.path.dirname(filename),f"{device_name}{str(number)}.log")

        
    if request.data:
        data = json.loads(request.data.decode())
        
        
    if data is None:
        # send the log file
        return 'no data'
    
    if data:
        # append to the data file
        if isinstance(data,dict) and 'device_name' in data and 'log' in data:
            filename = os.path.join(path,data['device_name']+'.log')
            # create the file if needed
            make_file(filename)
                    
            with open(filename,'a') as f:
                f.write(data['log'])
            
            # roll the log?
            size = os.stat(filename)[6]
            max_count = 4
            if size > 10000:
                # import pdb;pdb.set_trace()
                for i in range(max_count,0,-1):
                    log_name = get_log_name(filename,data['device_name'],i)
                    if os.path.exists(log_name):
                        if i == 4:
                            os.remove(log_name)
                        else:
                            new_log = log_name.replace(f"{data['device_name']}{str(i)}",f"{data['device_name']}{str(i+1)}")
                            if not os.path.exists(new_log):
                                os.rename(log_name,new_log)

                # current name.log becomes name_1.log
                log_name = get_log_name(filename,data['device_name'],1)
                os.rename(filename,log_name)
        
    return 'Ok'