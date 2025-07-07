
from django import template
from ..models import Player

register = template.Library()

@register.filter(name='get_player_by_zone')
def get_player_by_zone(players, zone):

    try:

        return players.filter(zone=zone).first()
    except AttributeError:
        
        pass
    return None
