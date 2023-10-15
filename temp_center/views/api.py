"""API to receive requests for access to the Temperature display devices"""

from flask import g, redirect, url_for, send_file, abort, \
    render_template, Blueprint, request

from shotglass2.shotglass import make_path, ShotLog
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.takeabeltof.date_utils import local_datetime_now
from shotglass2.users.admin import login_required, table_access_required
from temp_center.models import Device, Sensor, Reading

from datetime import datetime, timedelta
import os
import json
import hashlib

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


@mod.route('/get_file', methods=['POST'])
@mod.route('/get_file/', methods=['POST'])
def get_file():
    """Weather station device will post the filename and the
    hash of it's local file.
    If the hash of the file here does not match, 
    send our copy of the file.
    """
    
    if request.data:
        data = json.loads(request.data.decode())
    else:
        return ''
    
    if 'filename' in data and 'local_hash' in data:
        path = os.path.join('weather_station/app/',data['filename'])

        if not os.path.isfile(path):
            return abort(404)

        with open(path,'r') as f:
            my_hash = str(hashlib.sha1(f.read().encode()).digest())
        
        if my_hash != data['local_hash']:
            try:
                return send_file(path, as_attachment=True, max_age=0,)
            except:
                return abort(500)
        else:
            return ''
            
    return ''
    
@mod.route('/get_sensors/<int:device_id>', methods=['GET'])
def get_sensor_data(device_id):
    """Return a JSON string with details about the sensors"""

    sensors = Sensor(g.db).select(where=f'device_id={device_id}')
    if sensors:
        # need to convert DataRows into normal dicts
        l = []
        for sensor in sensors:
            d = {}
            for k,v in sensor.items():
                d.update({k:v})
            l.append(d)
        s = {'sensors':l}
        return json.dumps(s)
        
    return json.dumps({'sensors':[]})
        
    
@mod.route('/get_file/<path:path>', methods=['GET'])
def old_get_file(path):
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
@mod.route('/log/<device_id>', methods=['GET','POST'])
@mod.route('/log/<device_id>/', methods=['GET','POST'])
def log(device_id=None):
    """Record or get the remote log from the weather station"""

    def make_file(filename):
        # create the file if needed
        if not os.path.exists(filename):
            if make_path(filename):
                with open(filename,'w') as f:
                    f.close()
        
    def get_filename(path,device_id):
        return os.path.join(path,str(device_id),get_device_name(device_id) + '.log').replace(' ','_').replace('"','_').replace("'",'_')
        
    def get_device_name(device_id):
        d = Device(g.db).get(cleanRecordID(device_id))
        if d:
            return d.name
        return ''
        
        
    # import pdb;pdb.set_trace()
    path = 'instance/remote_logs/'
    data = None
    g.title = f'Remote Log for Unknown device'
    
    # filename= os.path.join(path,'remote.log')
    
    if request.method.upper() == 'GET':
        #return the log
        log = None
        device_name = get_device_name(device_id)
        if device_name:
            filename= get_filename(path,device_id)
            
            g.title = f'Remote Log for {device_name}'
            # device_name = 'remote'
            if os.path.exists(filename):
                log = ShotLog(filename).get_text()
            else:
                log = None
        
        return render_template('home/log.html',log=log)
    
    if request.data:
        data = json.loads(request.data.decode())
        
        
    if data is None:
        # send the log file
        return 'no data'
    
    if data:
        # append to the data file
        if isinstance(data,dict) and 'device_id' in data and 'log' in data:
            # create the file if needed
            device_name = get_device_name(data['device_id'])
            filename = get_filename(path,data['device_id'])
            if device_name and filename:
                make_file(filename)
                    
                with open(filename,'a') as f:
                    f.write(data['log'])
            
                # truncate the log?
                size = os.stat(filename)[6]
                if size > 20000:
                    tmp_name = os.path.join(path,'tmp.log')
                    # import pdb;pdb.set_trace()
                    with open(filename,'r') as f:
                        with open(tmp_name,'w') as w:
                            # find a return char
                            f.seek(int(size/2))
                            char = ''
                            while char != '\n':
                                char = f.read(1)
                            out = True
                            while out:
                                out = f.readline()
                                w.write(out)
                                                
                    os.remove(filename)
                    os.rename(tmp_name,filename)
        
    return 'Ok'
    
    