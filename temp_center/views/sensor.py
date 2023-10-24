from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from temp_center.models import Sensor, Device, Calibration

PRIMARY_TABLE = Sensor

mod = Blueprint('sensor',__name__, template_folder='templates/', url_prefix='/sensor')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Sensor'


from shotglass2.takeabeltof.views import TableView


# this handles table list and record delete
@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
@mod.route('/',methods=['GET','POST',])
@table_access_required(PRIMARY_TABLE)
def display(path=None):
    # import pdb;pdb.set_trace()
    setExits()
    
    view = TableView(PRIMARY_TABLE,g.db)
    # optionally specify the list fields
    view.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-small','search':True},
            {'name':'name'},
            {'name':'scale'},
            {'name':'sort_order'},
            {'name':'device_id'}
        ]
    
    return view.dispatch_request()
    

## Edit the PRIMARY_TABLE
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)

    sensor = PRIMARY_TABLE(g.db)
    rec = None
    devices = Device(g.db).select()

    if rec_id == None:
        rec_id = request.form.get('id',request.args.get('id',-1))
        
    rec_id = cleanRecordID(rec_id)
    #import pdb;pdb.set_trace

    if rec_id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    cal = Calibration(g.db).select(where=f'sensor_id = {rec_id}')
    
    if rec_id == 0:
        rec = sensor.new()
    else:
        rec = sensor.get(rec_id)
        if not rec:
            flash("Unable to locate that record")
            return redirect(g.listURL)
        

    if request.form:
        sensor.update(rec,request.form)
        if validForm(rec):
            sensor.save(rec)
            g.db.commit()
            
            calibration = Calibration(g.db)
            # import pdb;pdb.set_trace()
            cal_id = request.form.getlist('cal_id')
            cal_raw = request.form.getlist('cal_raw_temperature')
            cal_obs = request.form.getlist('cal_observed_temperature')
            cal_action = request.form.getlist('cal_action')
            for i in range(len(cal_id)):
                c_id = cleanRecordID(cal_id[i])
                if 'delete_' + str(c_id) in cal_action:
                    calibration.delete(c_id)
                    continue
                elif c_id > 0:
                    cal = calibration.get(c_id)
                    try:
                        cal.raw_temperature = float(cal_raw[i])
                        cal.observed_temperature = float(cal_obs[i])
                        cal.save()
                    except:
                        continue
                else:
                    continue

            calibration.commit()
            
            # Add new readings?
            new_raw = request.form.getlist('new_raw_temperature')
            new_obs = request.form.getlist('new_observed_temperature')
            for i in range(len(new_raw)):
                try:
                    raw = float(new_raw[i])
                    obs = float(new_obs[i])
                except:
                    continue
                cal = calibration.new()
                cal.sensor_id = rec.id
                cal.raw_temperature = raw
                cal.observed_temperature = obs
                cal.save()
                
            calibration.commit()

            return redirect(g.listURL)

    # display form
    return render_template('sensor/sensor_edit.html', rec=rec,devices=devices,cal=cal)
    
    
def validForm(rec):
    # Validate the form
    goodForm = True
                
    return goodForm
    
    
