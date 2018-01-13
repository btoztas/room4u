import requests
from django.apps import AppConfig


class RoomsConfig(AppConfig):
    name = 'rooms'

#    def ready(self):
#        r = requests.get("https://fenix.tecnico.ulisboa.pt/api/fenix/v1/spaces/")
#        json = r.json()
