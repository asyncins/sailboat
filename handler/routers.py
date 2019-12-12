from common import app
from .index import IndexHandler
from .deploy import DeployHandler
from .timers import TimersHandler
from .record import RecordsHandler
from .loghandler import LogHandler
from .user import RegisterHandler, UserHandler, LoginHandler

app.add_url_rule('/', view_func=IndexHandler.as_view('/'))
app.add_url_rule('/deploy', view_func=DeployHandler.as_view('/deploy'))
app.add_url_rule('/timer', view_func=TimersHandler.as_view('/timer'))
app.add_url_rule('/record', view_func=RecordsHandler.as_view('/record'))
app.add_url_rule('/logs', view_func=LogHandler.as_view('/logs'))
app.add_url_rule('/reg', view_func=RegisterHandler.as_view('/reg'))
app.add_url_rule('/user', view_func=UserHandler.as_view('/user'))
app.add_url_rule('/login', view_func=LoginHandler.as_view('/login'))