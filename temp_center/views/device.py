from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from temp_center.models import Device

PRIMARY_TABLE = Device

mod = Blueprint('device',__name__, template_folder='templates/', url_prefix='/device')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Device'


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

    device = PRIMARY_TABLE(g.db)
    rec = None
    
    if rec_id == None:
        rec_id = request.form.get('id',request.args.get('id',-1))
        
    rec_id = cleanRecordID(rec_id)
    #import pdb;pdb.set_trace

    if rec_id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    if rec_id == 0:
        rec = device.new()
    else:
        rec = device.get(rec_id)
        if not rec:
            flash("Unable to locate that record")
            return redirect(g.listURL)

    if request.form:
        device.update(rec,request.form)
        if validForm(rec):
            device.save(rec)
            g.db.commit()

            return redirect(g.listURL)

    # display form
    return render_template('device/device_edit.html', rec=rec)
    
    
def validForm(rec):
    # Validate the form
    goodForm = True
                
    return goodForm
    
