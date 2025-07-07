# referee/templatetags/stats_tag.py
import logging
from django import template
from ..models import Player, Action

register = template.Library()
@register.simple_tag
def calculate_mvp(players_stats):
    if not players_stats:
        return None
    
    mvp = None
    max_score = -1000
    
    for stats in players_stats:
        player = stats['player']
        position = player.position
        
       
        weights = {
            'l': 1.2, 
            's': 1.5, 
            'oh': 1.0,
            'op': 1.1, 
            'mb': 1.0  
        }
        
 
        score = stats['efficiency'] * weights.get(position, 1.0)
  
        if position == 'l':
            score += stats['receive']['success'] * 0.5
            score += stats['dig']['success'] * 0.7
        elif position == 's':
            score += stats['set']['success'] * 0.8
            if 'ace_sets' in stats:
                score += stats['ace_sets'] * 1.5
        elif position == 'op':
            score += stats['attack']['success'] * 0.8
            score += stats['serve_points'] * 1.2
        else:
            score += stats['attack']['success'] * 0.6
            score += stats['block_points'] * 0.6
        
 
        score -= stats['errors'] * 0.8
        
        if score > max_score:
            max_score = score
            mvp = {
                'player': player,
                'position': player.get_position_display(),
                'efficiency': stats['efficiency'],
                'points': stats['total_points'],
                'score': round(score, 1)
            }
            

            if position == 'l':
                mvp['perfect_receptions'] = stats['receive']['success']
                mvp['digs'] = stats['dig']['success']
            elif position == 's' and 'ace_sets' in stats:
                mvp['ace_sets'] = stats['ace_sets']
    
    return mvp
