from flask import g, session, request, redirect, flash, abort, url_for, session
import os
from shotglass2 import shotglass
from shotglass2.users.models import User, Pref
from shotglass2.takeabeltof.database import Database
from shotglass2.takeabeltof.jinja_filters import register_jinja_filters
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.tools.views import tools
from shotglass2.users.admin import Admin
from shotglass2.users.models import User
from shotglass2.users.views import user
from shotglass2.users.views.login import setUserStatus

from temp_center.models import init_db as temp_center_init, Device, Sensor, Reading
from temp_center.views import home, device, sensor, reading, api

# Create app
app = shotglass.create_app(
        __name__,
        instance_path='instance',
        config_filename='site_settings.py',
        static_folder=None,
        )
    

def start_app():
    shotglass.start_logging(app) # This logs to general purpose log.log 
    initalize_base_tables()
    register_blueprints()
    
    # use os.path.normpath to resolve true path to data file when using '../' shorthand
    shotglass.start_backup_thread(
        os.path.normpath(
            os.path.join(
                app.root_path,shotglass.get_site_config()['DATABASE_PATH']
                )
            )
        )

@app.context_processor
def inject_site_config():
    # Add 'site_config' dict to template context
    return {'site_config':shotglass.get_site_config()}

register_jinja_filters(app)


def init_db(db=None):
    # to support old code
    initalize_base_tables(db)

def initalize_base_tables(db=None):
    """Place code here as needed to initialze all the tables for this site"""
    if not db:
        db = get_db()
        
    user.initalize_tables(db)
    
    ### setup any other tables you need here....
    temp_center_init(db)

    
def get_db(filespec=None):
    """Return a connection to the database.

    If the db path does not exist, create it and initialize the db"""

    if not filespec:
        filespec = shotglass.get_site_config()['DATABASE_PATH']

    # This is probobly a good place to change the
    # filespec if you want to use a different database
    # for the current request.

    # test the path, if not found, try to create it
    if shotglass.make_db_path(filespec):
        g.db = Database(filespec).connect()
        initalize_base_tables(g.db)
    
        return g.db
    else:
        # was unable to create a path to the database
        raise IOError("Unable to create path to () in app.get_db".format(filespec))

    
# @app.context_processor
# def inject_site_config():
#     # Add 'site_config' dict to template context
#     return {'site_config':shotglass.get_site_config()}


@app.before_request
def _before():
    # Force all connections to be secure
    if '/api/' not in request.url and \
        (app.config['REQUIRE_SSL'] and not request.is_secure):
        return redirect(request.url.replace("http://", "https://"))

    #ensure that nothing is served from the instance directory
    if 'instance' in request.url:
        return abort(404)
        
    # import pdb;pdb.set_trace()
    # print(app.url_map)
    session.permanent = True
    
    shotglass.set_template_dirs(app)
    get_db()

    if 'static' in request.url:
        return
    
    # load the saved visit_data into session
    shotglass._before_request(g.db)

    # Is the user signed in?
    g.user = None
    is_admin = False
    if 'user_id' in session and 'user' in session:
        # Refresh the user session
        setUserStatus(session['user'],cleanRecordID(session['user_id']))
        is_admin = User(g.db).is_admin(session['user_id'])

    # if site is down and user is not admin, stop them here.
    # will allow an admin user to log in
    down = Pref(g.db).get("Site Down Till",
                        user_name=shotglass.get_site_config().get("HOST_NAME"),
                        default='',
                        description = 'Enter something that looks like a date or time. It will be displayed to visitors and make the site inaccessable. Delete the value to allow access again.',
                        )
    if down and down.value.strip():
        if not is_admin:
            # log the user out...
            from shotglass2.users.views import login
            if g.user:
                login.logout()

            # this will allow an admin to log in.
            if request.url.endswith(url_for('login.login')):
                return login.login()
            
            g.title = "Sorry"
            return render_template('site_down.html',down_till = down.value.strip())
        else:
            flash("The Site is in Maintenance Mode. Changes may be lost...",category='warning')

    create_menus()

        

def create_menus():
    # g.menu_items should be a list of dicts
    #  with keys of 'title' & 'url' used to construct
    #  the non-table based items in the main menu
    g.menu_items = [
        {'title':'Home','url':url_for('home.home')},
        # {'title':'About','url':url_for('www.about')},
        # {'title':'Contact Us','url':url_for('www.contact')},
        ]
        
    # g.admin items are added to the navigation menu by default
    g.admin = Admin(g.db) # This is where user access rules are stored
    
    # # Add a module to the menu
    g.admin.register(Device,
                     None,
                     display_name='Temp Center',
                     top_level=False,
                     header_row=True,
                     minimum_rank_required=500,
                     )

    g.admin.register(Device,
                     url_for('api.log')+'/1',
                     display_name='Remote Log',
                     top_level=False,
                     minimum_rank_required=500,
                     )
                     
    g.admin.register(Device,
                     url_for('device.display'),
                     display_name='Devices',
                     top_level=False,
                     minimum_rank_required=500,
                     )
    g.admin.register(Sensor,
                url_for('sensor.display'),
                display_name='Sensors',
                top_level=False,
                minimum_rank_required=500,
        )
    g.admin.register(Reading,
            url_for('reading.display'),
            display_name='Readings',
            top_level=False,
            minimum_rank_required=500,
        )
    
    # This one will set up the view log item
    g.admin.register(User,
            url_for('tools.view_log'),
            display_name='View Log',
            top_level = True,
            minimum_rank_required=500,
        )
    
    
    # shotglass.user_setup() # g.admin now holds access rules Users, Prefs and Roles
    # set up the User menu
    user.create_menus()

@app.teardown_request
def _teardown(exception):
    if 'db' in g:
        g.db.close()


@app.errorhandler(404)
def page_not_found(error):
    return shotglass.page_not_found(error)

@app.errorhandler(500)
def server_error(error):
    return shotglass.server_error(error)

#Register the static route
app.add_url_rule('/static/<path:filename>','static',shotglass.static)

# To use a different subdomain as asset server, use this instead
# Direct to a specific server for static content
#app.add_url_rule('/static/<path:filename>','static',shotglass.static,subdomain="somesubdomain")


# ## Setup the routes for users
# #shotglass.register_users(app)

# users.register_users
# # setup www.routes...
# # shotglass.register_www(app)

# app.register_blueprint(tools.mod)

# # # add more modules...
# app.register_blueprint(home.mod)
# app.register_blueprint(device.mod)
# app.register_blueprint(sensor.mod)
# app.register_blueprint(reading.mod)
# app.register_blueprint(api.mod)

def register_blueprints():
    """Register all your blueprints here and initialize 
    any data tables they need.
    """

    user.register_blueprints(app)
    # shotglass.register_www(app)
    app.register_blueprint(tools.mod)

    # # add more modules...
    app.register_blueprint(home.mod)
    app.register_blueprint(device.mod)
    app.register_blueprint(sensor.mod)
    app.register_blueprint(reading.mod)
    app.register_blueprint(api.mod)

with app.app_context():
    start_app()

if __name__ == '__main__':
    
    with app.app_context():
        # create the default database if needed
        initalize_base_tables()
        
    app.run(host='127.0.0.1', port=5000)
    # app.run()
    
    
