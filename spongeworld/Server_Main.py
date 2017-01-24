from flask import Flask, g
from spongeworld import Sponge_Flask_Obj
from database import DBData

from utils import debug, SetDebugLevel

app = Flask(__name__)
app.register_blueprint(Sponge_Flask_Obj)

SetDebugLevel(0)
print('hello')
debug(6, 'loading database')
# init the global database structure
dbdata = DBData()
dbdata.import_data()
debug(6, 'starting server')


# whenever a new request arrives, connect to the database and store in g.db
@app.before_request
def before_request():
    global dbdata

    g.db = dbdata


# and when the request is over, disconnect
@app.teardown_request
def teardown_request(exception):
    pass


if __name__ == '__main__':
    app.run(debug=True)
