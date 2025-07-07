from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator  
from django.utils import timezone
from django.db import transaction
class Team(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        error_messages={
            'unique': 'Команда с таким названием уже существует'
        }
    )
    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'

    def clean(self):
        if any(char.isdigit() for char in self.name):
            raise ValidationError(_("Название команды не должно содержать цифр"))
        
        if not self.name.strip():
            raise ValidationError(_("Название команды не может быть пустым"))
    def __str__(self):
        return self.name


class Player(models.Model):
    POSITION_CHOICES = [
        ('s', 'связующий'),
        ('oh', 'доигровщик'),
        ('op', 'диагональный'),
        ('mb', 'центральный блокирующий'),
        ('l', 'либеро'),
    ]
    
    TEAM_CHOICES = [
        ('A', 'Team A'),
        ('B', 'Team B'),
    ]
    
    team = models.ForeignKey(
        'Team', 
        related_name='players', 
        on_delete=models.CASCADE,
        verbose_name='Команда'
    )
    match = models.ForeignKey(
        'Match', 
        on_delete=models.CASCADE,
        verbose_name='Матч'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Имя игрока'
    )
    number = models.PositiveIntegerField(
        verbose_name='Номер'
    )
    position = models.CharField(
        max_length=2, 
        choices=POSITION_CHOICES,
        verbose_name='Позиция'
    )
    zone = models.CharField(
        max_length=1,
        null=True,  
        blank=True,
        verbose_name='Зона'
    
    )
    team_choice = models.CharField(
        max_length=1, 
        choices=TEAM_CHOICES,
        verbose_name='Выбор команды'
    )
    is_captain = models.BooleanField(
        default=False,
        verbose_name='Капитан'
    )
    
        
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['match', 'team', 'zone'],
                name='unique_player_zone_per_team_match'
            )
        ]
        ordering = ['team_choice', 'number']
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'
        unique_together = [
            ('match', 'team', 'number'), 
            ('match', 'team', 'zone')     
        ]
        models.UniqueConstraint(
            fields=['match', 'team'],
            condition=models.Q(is_captain=True),
            name='unique_captain_per_team_match'
            ),
        models.UniqueConstraint(
            fields=['match', 'team'],
            condition=models.Q(position='l'),
            name='unique_libero_per_team_match'
            )

    def __str__(self):
        return f"{self.name} (#{self.number}, {self.get_position_display()})"

class Match(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Не начат'),
        ('started', 'Начат'),
        ('finished', 'Завершён'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    
    team_a = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='matches_as_team_a'
    )
    
    team_b = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='matches_as_team_b'
    )
    
    team_a_score = models.PositiveIntegerField(default=0)
    team_b_score = models.PositiveIntegerField(default=0)
    
    current_set = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team_a} vs {self.team_b} (Status: {self.get_status_display()})"

    team_a_rotation = models.JSONField(default=dict)  
    team_b_rotation = models.JSONField(default=dict)
    
    def initialize_rotations(self):
        self.team_a_rotation = {
            str(player.zone): player.id 
            for player in self.team_a.players.filter(match=self)
        }
        
        self.team_b_rotation = {
            str(player.zone): player.id 
            for player in self.team_b.players.filter(match=self)
        }
        self.save()
    
    def _get_initial_rotation(self, team):
        players = team.players.filter(match=self)
        return {str(p.zone): p.id for p in players}
    
    def rotate_team(self, team):
        rotation = self.team_a_rotation if team == self.team_a else self.team_b_rotation
        
        new_rotation = {
            '6': rotation.get('1'),
            '1': rotation.get('2'),
            '2': rotation.get('3'),
            '3': rotation.get('4'),
            '4': rotation.get('5'),
            '5': rotation.get('6')
        }
        
        players = Player.objects.filter(team=team, match=self)
        with transaction.atomic():
            players.update(zone=None)
            
            for zone, player_id in new_rotation.items():
                if player_id:
                    Player.objects.filter(id=player_id).update(zone=zone)
        
        if team == self.team_a:
            self.team_a_rotation = new_rotation
        else:
            self.team_b_rotation = new_rotation
            
        self.save()
    current_set = models.PositiveIntegerField(default=1)
    sets_won_a = models.PositiveIntegerField(default=0)
    sets_won_b = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    MAX_SETS = 3  
    POINTS_TO_WIN_SET = 25  
    POINTS_TO_WIN_TIEBREAK = 15 
    
    def check_set_completion(self):
        if self.is_completed:
            return
            
        points_to_win = self.POINTS_TO_WIN_TIEBREAK if self.current_set == 3 else self.POINTS_TO_WIN_SET
        
        if self.team_a_score >= points_to_win and self.team_a_score >= self.team_b_score + 2:
            self.sets_won_a += 1
            self._finish_set()
        elif self.team_b_score >= points_to_win and self.team_b_score >= self.team_a_score + 2:
            self.sets_won_b += 1
            self._finish_set()
            
    def _finish_set(self):
        if self.sets_won_a >= 2 or self.sets_won_b >= 2:  
            self.is_completed = True
        else:
            self.current_set += 1
            self.team_a_score = 0
            self.team_b_score = 0
        self.save()
    def can_start(self):
        return (self.team_a.players.filter(match=self).count() == 6 and 
                self.team_b.players.filter(match=self).count() == 6)
    
    def start_match(self):
        if self.status == 'not_started':
            self.status = 'started'
            self.start_time = timezone.now()
            self.initialize_rotations()
            self.save()

class Action(models.Model):
    ACTION_TYPE_CHOICES = [
        ('serve', 'Подача'),
        ('attack', 'Атака'),
        ('block', 'Блок'),
        ('receive', 'Прием'),
        ('set', 'Пас'),
        ('dig', 'Защита'),
        ('error', 'Ошибка'),
    ]
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    action_type = models.CharField(max_length=12, choices=ACTION_TYPE_CHOICES)
    success = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        scoring_team = None
        
        if self.player:
            try:
                if self.action_type == 'error':
                    scoring_team = self.match.team_b if self.player.team == self.match.team_a else self.match.team_a
                elif self.success and self.action_type in ['serve', 'attack', 'block']:
                    scoring_team = self.player.team
                    
                if scoring_team:
                    if scoring_team == self.match.team_a:
                        self.match.team_a_score += 1
                    else:
                        self.match.team_b_score += 1
                    self.match.save()
                    self.match.rotate_team(scoring_team)
                    self.match.check_set_completion()
                    self.match.save()
            except Exception as e:
                logging.error(f"Error in Action.save: {e}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.timestamp}"

class PlayerStats(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    
    points = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)
    
    attacks = models.PositiveIntegerField(default=0)
    blocks = models.PositiveIntegerField(default=0)
    
    perfect_receptions = models.PositiveIntegerField(default=0)
    digs = models.PositiveIntegerField(default=0)
    reception_errors = models.PositiveIntegerField(default=0)
    total_receptions = models.PositiveIntegerField(default=0)
    
    successful_sets = models.PositiveIntegerField(default=0)
    ace_sets = models.PositiveIntegerField(default=0)
    set_errors = models.PositiveIntegerField(default=0)
    attack_distribution = models.PositiveIntegerField(default=0) 


 