import logging
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django import forms
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import DatabaseError, IntegrityError
from django.contrib import messages
from .models import Match, Player, Team, Action
from .forms import TeamForm, PlayerForm, ActionForm
from django.http import JsonResponse
logger = logging.getLogger(__name__)

def handle_404(request, exception):
    logger.warning(f"404 error: {exception}")
    return HttpResponseNotFound(render(request, 'referee/404.html'))


class MatchSetupView(View):
    def get(self, request):
        try:
            form = TeamForm()
            return render(request, 'referee/match_setup.html', {'form': form})
        except Exception as e:
            logger.error(f"Error in MatchSetupView GET: {str(e)}")
            messages.error(request, "Произошла ошибка при загрузке формы")
            return redirect('home')
    

    def post(self, request):
        form = TeamForm(request.POST)
        if form.is_valid():
            team_a_name = form.cleaned_data['team_a_name']
            team_b_name = form.cleaned_data['team_b_name']
            if team_a_name.lower() == team_b_name.lower():
                form.add_error('team_b_name', "Названия команд должны отличаться")
                return render(request, 'referee/match_setup.html', {'form': form})

            team_a, _ = Team.objects.get_or_create(name=team_a_name)
            team_b, _ = Team.objects.get_or_create(name=team_b_name)
            team_choice = forms.ChoiceField(choices=[('A', 'Team A'), ('B', 'Team B')])
            match = Match.objects.create(team_a=team_a, team_b=team_b)
            return redirect('add_players', match_id=match.id)
    
        return render(request, 'referee/match_setup.html', {'form': form})
        
class AddPlayersView(View):
   def get(self, request, match_id):
        match = get_object_or_404(Match, id=match_id)
        form = PlayerForm()
        can_start_match = self._check_teams_ready(match)
        context = {
            'form': form,
            'match': match,
            'team_a_players': match.team_a.players.all(),  
            'team_b_players': match.team_b.players.all(),  
            'team_a_zones': {p.zone: p for p in match.team_a.players.all()},
            'team_b_zones': {p.zone: p for p in match.team_b.players.all()},
            'court_zones': {
                'front': ['4', '3', '2'],
                'back': ['5', '6', '1'],
                
            },
            'can_start_match': can_start_match,
        }
        return render(request, 'referee/add_players.html', context)

   def post(self, request, match_id):
        match = get_object_or_404(Match, id=match_id)
        form = PlayerForm(request.POST, match=match)

        if form.is_valid():
            try:
                player = form.save(commit=False)
                team_choice = form.cleaned_data['team_choice']
                player.team = match.team_a if team_choice == 'A' else match.team_b
                player.save()
                return redirect('add_players', match_id=match.id)
            except ValidationError as e:
                messages.error(request, 'Ошибка валидации: ' + str(e))
            except Exception as e:
                messages.error(request, 'Произошла ошибка: ' + str(e))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        return redirect('add_players', match_id=match.id)


   def _check_teams_ready(self, match):
        return (match.team_a.players.count() == 6 and 
                match.team_b.players.count() == 6)
   
def add_player(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    
    if request.method == 'POST':
        form = PlayerForm(request.POST, match=match)
        if form.is_valid():
            player = form.save(commit=False)
            player.match = match
            player.save()
            return redirect('players_list', match_id=match.id)
    else:
        form = PlayerForm(match=match)
    
    return render(request, 'referee/add_players.html', {
        'form': form,
        'match': match
    })
class MatchControlView(View):
    def get(self, request, match_id):
       
            match = get_object_or_404(Match, id=match_id)
            
            if not hasattr(match, 'team_a_rotation') or not match.team_a_rotation:
                match.team_a_rotation = {}
            if not hasattr(match, 'team_b_rotation') or not match.team_b_rotation:
                match.team_b_rotation = {}
                
            if not match.team_a_rotation or not match.team_b_rotation:
                match.initialize_rotations()
            
            players_stats = []
            players = Player.objects.filter(match=match)
    
            for player in players:
                actions = Action.objects.filter(player=player)
        
                stats = {
                    'player': player,
                    'total_actions': actions.count(),
                    'serve': {'total': 0, 'success': 0, 'errors': 0},
                    'attack': {'total': 0, 'success': 0, 'errors': 0},
                    'block': {'total': 0, 'success': 0, 'errors': 0},
                    'receive': {'total': 0, 'success': 0, 'errors': 0},
                    'set': {'total': 0, 'success': 0, 'errors': 0},
                    'dig': {'total': 0, 'success': 0, 'errors': 0},
                    'errors': 0,
                    'total_points': 0,
                    'efficiency': 0.0
                }
        
                for action in actions:
                    atype = action.action_type
            
                    if atype in stats:
                        stats[atype]['total'] += 1
            
                    if action.success:
                        if atype in ['serve', 'attack', 'block']:
                            stats['total_points'] += 1
                
                        if atype in stats:
                            stats[atype]['success'] += 1
                    else:
                       
                        if atype == 'error':
                            stats['errors'] += 1
                        elif atype in stats:
                            stats[atype]['errors'] += 1
        
                
                efficiency = 0.0
                total_positive = stats['total_points']
                total_actions = stats['total_actions']
        
                if player.position == 'l':
                   
                    receive = stats['receive']['success']
                    digs = stats['dig']['success']
                    efficiency = (receive * 0.5 + digs * 0.3) / max(1, stats['receive']['total'] + stats['dig']['total']) * 100
                elif player.position == 's':
                    
                    success_sets = stats['set']['success']
                    stats['ace_sets'] = success_sets  
                    efficiency = (success_sets) / max(1, stats['set']['total']) * 60
                else:
                    
                    attack = stats['attack']['success'] + stats['attack']['total'] * 0.1
                    block = stats['block']['success'] + stats['block']['total'] * 0.1
                    serve = stats['serve']['success'] + stats['serve']['total'] * 0.2
            
                    if player.position == 'mb':
                        efficiency = (attack * 0.3 + block * 0.5 + serve * 0.2) / max(1, total_actions) * 100
                    else:
                        efficiency = (attack * 0.4 + block * 0.3 + serve * 0.3) / max(1, total_actions) * 100
        
                stats['attack_points'] = stats['attack']['success']
                stats['block_points'] = stats['block']['success']
                stats['serve_points'] = stats['serve']['success']
        
                stats['efficiency'] = min(100, max(0, efficiency))
                players_stats.append(stats)
            
            context = {
                'match': match,
                'action_form': ActionForm(match=match),
                'players_stats': players_stats,
                'actions': actions,
            }
            return render(request, 'referee/match_control.html', context)
           

    def post(self, request, match_id):
        logger.info(f"POST request for match {match_id}: {request.POST}")
        try:
            match = Match.objects.get(id=match_id)
            
            if match.is_completed:
                messages.warning(request, "Матч уже завершен")
                return redirect('match_control', match_id=match.id)
            
            if 'action' in request.POST:
                form = ActionForm(request.POST, match=match)
                if form.is_valid():
                    try:
                        action = form.save(commit=False)
                        action.match = match
                        action.save()
                        
                    except Exception as e:
                        logger.error(f"Error saving action: {e}")
                        messages.error(request, f'Ошибка: {str(e)}')
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'{field}: {error}')
                            
            
           
            elif 'point_team_a' in request.POST:
                match.save()
                match.rotate_team(match.team_a)
                
            
            elif 'point_team_b' in request.POST:
                match.team_b_score += 1
                match.save()
                match.rotate_team(match.team_b)
                
            
           
            match.check_set_completion()
            return redirect('match_control', match_id=match.id)
            
        except Match.DoesNotExist:
            logger.error(f"Match not found: {match_id}")
            return HttpResponseNotFound("Матч не найден")
        except Exception as e:
            logger.exception(f"Error in MatchControlView POST: {e}")
            return HttpResponseServerError("Внутренняя ошибка сервера")


class StartMatchView(View):
     def post(self, request, match_id):
        match = get_object_or_404(Match, id=match_id)
        
        if not match.can_start():
            messages.error(request, "Нельзя начать матч: в каждой команде должно быть 6 игроков")
            return redirect('add_players', match_id=match.id)
        
        if match.status != 'not_started':
            messages.warning(request, "Матч уже начат или завершен")
            return redirect('match_control', match_id=match.id)
        
        match.start_match()
        messages.success(request, "Матч успешно начат!")
        return redirect('match_control', match_id=match.id)

# def calculate_stats(match):
#     players_stats = []
#     for player in match.players.all():
#         actions = Action.objects.filter(match=match, player=player)
        
#         stats = {
#             'player': player,
#             'total_actions': actions.count(),
#             'points': 0,
#             'successful_actions': 0,
#             'errors': 0,
#             'perfect_receptions': 0,
#             'digs': 0,
#             'ace_sets': 0
#         }
        
#         for action in actions:
#             if action.success:
#                 if action.action_type in ['attack', 'block', 'serve']:
#                     stats['points'] += 1
#                 stats['successful_actions'] += 1
                
#                 if player.position == 'l' and action.action_type == 'reception':
#                     stats['perfect_receptions'] += 1
#                 elif player.position == 's' and action.action_type == 'set':
#                     stats['ace_sets'] += 1
#             else:
#                 stats['errors'] += 1
        
#         players_stats.append(stats)
    
#     return players_stats




