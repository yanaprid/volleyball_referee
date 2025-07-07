document.addEventListener('DOMContentLoaded', function () {
    try {
        // Динамическое обновление страницы каждые 30 секунд
        const refreshInterval = setInterval(function () {
            window.location.reload();
        }, 30000);

        // Обработка формы действий
        const actionForm = document.getElementById('action-form');
        if (actionForm) {
            const actionTypeSelect = actionForm.querySelector('select[name="action_type"]');
            const successField = actionForm.querySelector('#id_success').closest('.form-group');
            const playerField = actionForm.querySelector('#id_player').closest('.form-group');

            if (actionTypeSelect && successField && playerField) {
                actionTypeSelect.addEventListener('change', function () {
                    const actionType = this.value;

                    // Скрываем/показываем поля в зависимости от типа действия
                    if (actionType === 'timeout' || actionType === 'substitution') {
                        successField.style.display = 'none';
                    } else {
                        successField.style.display = 'block';
                    }

                    if (actionType === 'timeout') {
                        playerField.style.display = 'none';
                    } else {
                        playerField.style.display = 'block';
                    }
                });

                // Инициализация состояния при загрузке
                const event = new Event('change');
                actionTypeSelect.dispatchEvent(event);
            } else {
                console.error('Не найдены необходимые элементы формы действий');
            }
        }

        // Обработка формы замен
        const substitutionForm = document.getElementById('substitution-form');
        if (substitutionForm) {
            substitutionForm.addEventListener('submit', function (e) {
                const playerOut = this.querySelector('select[name="player_out"]').value;
                const playerIn = this.querySelector('select[name="player_in"]').value;

                if (!playerOut || !playerIn) {
                    e.preventDefault();
                    alert('Пожалуйста, выберите обоих игроков для замены!');
                }
            });
        }

        // Подсветка зоны подачи
        function highlightServingZone() {
            try {
                const servingBadge = document.querySelector('.serving-team .badge');
                if (!servingBadge) return;

                const servingTeam = servingBadge.textContent;
                const zones = document.querySelectorAll('.court-zone');

                zones.forEach(zone => {
                    zone.classList.remove('serving-zone');
                    if (zone.classList.contains('zone-1')) {
                        const isTeamA = zone.closest('.team-a-court') && servingTeam.includes(match.team_a.name);
                        const isTeamB = zone.closest('.team-b-court') && servingTeam.includes(match.team_b.name);

                        if (isTeamA || isTeamB) {
                            zone.classList.add('serving-zone');
                        }
                    }
                });
            } catch (e) {
                console.error('Ошибка при подсветке зоны подачи:', e);
            }
        }

        highlightServingZone();

        // Обработка ошибок при загрузке данных
        window.addEventListener('error', function (e) {
            console.error('Произошла ошибка:', e.message);
            // Можно добавить отображение пользователю, если нужно
        });

        // Очистка интервала при разгрузке страницы
        window.addEventListener('beforeunload', function () {
            clearInterval(refreshInterval);
        });

    } catch (e) {
        console.error('Произошла критическая ошибка в скрипте:', e);
    }
});