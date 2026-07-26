"""Activities and teams page shell."""

from PySide6.QtWidgets import QHBoxLayout

from ..widgets import Card, PageScaffold, PlaceholderTable, PrimaryButton


class ActivitiesPage(PageScaffold):
    def __init__(self):
        super().__init__(
            "ATIVIDADES (TIMES)",
            "Gerencie os times, participantes e pontos do acampamento.",
            "♜",
        )

        upper = QHBoxLayout()
        upper.setSpacing(16)

        create_team = Card("CRIAR TIME", "Use esta ação para criar um novo time.")
        create_team.body.addWidget(PrimaryButton("＋  Novo Time"))
        upper.addWidget(create_team, 2)

        participants = Card(
            "GERENCIAR PARTICIPANTES DO TIME SELECIONADO",
            "Adicione ou remova participantes de um time já existente.",
        )
        participant_actions = QHBoxLayout()
        participant_actions.addWidget(PrimaryButton("＋  Adicionar Participante"))
        participant_actions.addWidget(PrimaryButton("Remover Participante"))
        participants.body.addLayout(participant_actions)
        upper.addWidget(participants, 3)
        self.content.addLayout(upper)

        team_area = Card()
        actions = QHBoxLayout()
        actions.addWidget(PrimaryButton("＋  Adicionar Pontos"))
        actions.addWidget(PrimaryButton("Remover Time"))
        actions.addStretch(1)
        team_area.body.addLayout(actions)
        table = PlaceholderTable(
            ["Time", "Capitão", "Participantes", "Pontos", "Ação"],
            rows=3,
        )
        team_area.body.addWidget(table)
        self.content.addWidget(team_area)
        self.content.addStretch(1)

