from django.core.management.base import BaseCommand
import requests
from rooms.models import Room


class Command(BaseCommand):

    base_url = 'https://fenix.tecnico.ulisboa.pt/api/fenix/v1/spaces/'

    def retrieve_space(self, space_parent, space_to_explore, hierarchy):

        # Request space's info
        r = requests.get(self.base_url + space_to_explore)
        space_info = r.json()

        # Create new space object with the info retrieved
        if space_parent == 0:
            new_space = Room(id=space_info['id'], name=space_info['name'], hierarchy=hierarchy)
        else:
            new_space = Room(id=space_info['id'], parent_id=space_parent,
                             name=space_info['name'], hierarchy=hierarchy)
        new_space.save()

        hierarchy = hierarchy + '/' + space_info['name']

        # Explore other contained spaces within this space
        for contained_space in space_info['containedSpaces']:
            self.retrieve_space(space_to_explore=contained_space['id'], space_parent=new_space, hierarchy=hierarchy)

    def handle(self, *args, **options):

        if not Room.objects.all().exists():

            # Request space's info - this will be the campuses (roots of the tree)
            r = requests.get(self.base_url)
            campuses = r.json()

            # Explore spaces contained within the campus
            for campus_index in range(0, len(campuses)):
                campus_id = campuses[campus_index]['id']
                hierarchy = ''
                self.retrieve_space(space_to_explore=campus_id, space_parent=0, hierarchy=hierarchy)
