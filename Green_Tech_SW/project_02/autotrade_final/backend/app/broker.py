import os
from .kis_client import KISBroker
from .paper_broker import PaperBroker

def get_broker():
    name = os.getenv("BROKER", "PAPER").upper()
    if name == "KIS":
        return KISBroker()
    return PaperBroker()
