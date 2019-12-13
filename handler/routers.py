from common import app
from .index import IndexHandler
from .deploy import DeployHandler
from .timers import TimersHandler
from .record import RecordsHandler
from .loghandler import LogHandler
from .user import RegisterHandler, UserHandler, LoginHandler

version = "/api/v1"

app.add_url_rule(version + '/work', view_func=IndexHandler.as_view(version + '/work'))
app.add_url_rule(version + '/deploy', view_func=DeployHandler.as_view(version + '/deploy'))
app.add_url_rule(version + '/timer', view_func=TimersHandler.as_view(version + '/timer'))
app.add_url_rule(version + '/record', view_func=RecordsHandler.as_view(version + '/record'))
app.add_url_rule(version + '/logs', view_func=LogHandler.as_view(version + '/logs'))
app.add_url_rule(version + '/reg', view_func=RegisterHandler.as_view(version + '/reg'))
app.add_url_rule(version + '/user', view_func=UserHandler.as_view(version + '/user'))
app.add_url_rule(version + '/login', view_func=LoginHandler.as_view(version + '/login'))