document.addEventListener('DOMContentLoaded', function () {
    try {
        // ������������ ���������� �������� ������ 30 ������
        const refreshInterval = setInterval(function () {
            window.location.reload();
        }, 30000);

        // ��������� ����� ��������
        const actionForm = document.getElementById('action-form');
        if (actionForm) {
            const actionTypeSelect = actionForm.querySelector('select[name="action_type"]');
            const successField = actionForm.querySelector('#id_success').closest('.form-group');
            const playerField = actionForm.querySelector('#id_player').closest('.form-group');

            if (actionTypeSelect && successField && playerField) {
                actionTypeSelect.addEventListener('change', function () {
                    const actionType = this.value;

                    // ��������/���������� ���� � ����������� �� ���� ��������
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

                // ������������� ��������� ��� ��������
                const event = new Event('change');
                actionTypeSelect.dispatchEvent(event);
            } else {
                console.error('�� ������� ����������� �������� ����� ��������');
            }
        }

        // ��������� ����� �����
        const substitutionForm = document.getElementById('substitution-form');
        if (substitutionForm) {
            substitutionForm.addEventListener('submit', function (e) {
                const playerOut = this.querySelector('select[name="player_out"]').value;
                const playerIn = this.querySelector('select[name="player_in"]').value;

                if (!playerOut || !playerIn) {
                    e.preventDefault();
                    alert('����������, �������� ����� ������� ��� ������!');
                }
            });
        }

        // ��������� ���� ������
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
                console.error('������ ��� ��������� ���� ������:', e);
            }
        }

        highlightServingZone();

        // ��������� ������ ��� �������� ������
        window.addEventListener('error', function (e) {
            console.error('��������� ������:', e.message);
            // ����� �������� ����������� ������������, ���� �����
        });

        // ������� ��������� ��� ��������� ��������
        window.addEventListener('beforeunload', function () {
            clearInterval(refreshInterval);
        });

    } catch (e) {
        console.error('��������� ����������� ������ � �������:', e);
    }
});