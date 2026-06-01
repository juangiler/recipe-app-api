from uvicorn.workers import UvicornWorker


class UvicornWorkerLifespanOff(UvicornWorker):
    CONFIG_KWARGS = {"lifespan": "off"}
