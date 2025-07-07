from django import forms
from django.core.exceptions import ValidationError
from .models import Player, Match, Team , Action, PlayerStats

class TeamForm(forms.Form):
    team_a_name = forms.CharField(
        label='Команда A', 
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Пожалуйста, введите название команды A',
            'max_length': 'Название команды слишком длинное'
        }
    )
    team_b_name = forms.CharField(
        label='Команда B', 
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Пожалуйста, введите название команды B',
            'max_length': 'Название команды слишком длинное'
        }
    )
    def clean_team_a_name(self):
        name = self.cleaned_data['team_a_name'].strip()
        if not name:
            raise ValidationError("Название команды A не может быть пустым")
        if any(char.isdigit() for char in name):
            raise ValidationError("Название команды не должно содержать цифр")
        return name

    def clean_team_b_name(self):
        name = self.cleaned_data['team_b_name'].strip()
        if not name:
            raise ValidationError("Название команды B не может быть пустым")
        if any(char.isdigit() for char in name):
            raise ValidationError("Название команды не должно содержать цифр")
        return name

    def clean(self):
        cleaned_data = super().clean()
        team_a_name = cleaned_data.get('team_a_name')
        team_b_name = cleaned_data.get('team_b_name')
        
        if team_a_name and team_b_name and team_a_name.lower() == team_b_name.lower():
            raise ValidationError("Названия команд должны отличаться")
        
        return cleaned_data


class PlayerForm(forms.ModelForm):
    team_choice = forms.ChoiceField(choices=[('A', 'Team A'), ('B', 'Team B')], label="Команда")
    
    class Meta:
        model = Player
        fields = ['name', 'number', 'position', 'zone', 'is_captain']
        
    def __init__(self, *args, **kwargs):
        self.match = kwargs.pop('match', None)
        super().__init__(*args, **kwargs)
        
        if self.match:
            self.fields['team_choice'].choices = [
                ('A', f'Команда {self.match.team_a.name}'),
                ('B', f'Команда {self.match.team_b.name}')
            ]
    def clean(self):
        cleaned_data = super().clean()
        zone = cleaned_data.get('zone')
        team_choice = cleaned_data.get('team_choice')
        match = self.match
        position = cleaned_data.get('position')
        is_captain = cleaned_data.get('is_captain', False)
        if zone and team_choice and match:
            team = match.team_a if team_choice == 'A' else match.team_b
            if Player.objects.filter(
                match=match,
                team=team,
                zone=zone
            ).exists():
                raise forms.ValidationError(
                    f'В зоне {zone} уже есть игрок команды {team.name}'
                )

        if is_captain and Player.objects.filter(
            match=match,
            team=team,
            is_captain=True
        ).exists():
            raise forms.ValidationError(
                f'В команде {team.name} уже есть капитан'
            )
        
        if position == 'l' and Player.objects.filter(
            match=match,
            team=team,
            position='l'
        ).exists():
            raise forms.ValidationError(
                f'В команде {team.name} уже есть либеро'
            )
        
        
        return cleaned_data
    def save(self, commit=True):
        player = super().save(commit=False)
        player.match = self.match
        team_choice = self.cleaned_data['team_choice']
        player.team = self.match.team_a if team_choice == 'A' else self.match.team_b
        
        if commit:
            player.save()
        return player


class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['player', 'action_type', 'success']

    def __init__(self, *args, **kwargs):
        match = kwargs.pop('match', None)
        super().__init__(*args, **kwargs)
        if match:
            
            self.fields['player'].queryset = Player.objects.filter(
                team__in=[match.team_a, match.team_b]
            )













