from handler.routers import app

from common import scheduler


if __name__ == "__main__":
    scheduler.start()
    app.run(debug=True)
