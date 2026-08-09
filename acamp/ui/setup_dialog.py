"""Guided packaged-data setup without exposing private contents."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from acamp.paths import ApplicationPaths
from acamp.runtime_data import (
    REQUIRED_DATA_FILES,
    import_runtime_files,
    missing_required_files,
    present_optional_files,
)

from .widgets import PrimaryButton


class RuntimeDataSetupDialog(QDialog):
    """Let the user select a folder or explicitly import runtime files."""

    def __init__(
        self,
        paths: ApplicationPaths,
        parent=None,
    ):
        super().__init__(parent)
        self._paths = paths
        self._store = paths.data_config_store
        self._managed_root = paths.managed_root

        self.setObjectName("dataSetupDialog")
        self.setWindowTitle("Configurar dados do ACAMP")
        self.setModal(True)
        self.setMinimumWidth(720)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Configure os dados desta aplicação")
        title.setObjectName("setupTitle")
        layout.addWidget(title)

        introduction = QLabel(
            "Escolha uma pasta que já contenha os dados do ACAMP ou "
            "importe arquivos selecionados para a pasta privada desta "
            "aplicação. Nenhum conteúdo será exibido ou enviado."
        )
        introduction.setObjectName("setupIntroduction")
        introduction.setWordWrap(True)
        layout.addWidget(introduction)

        choices = QHBoxLayout()
        choices.setSpacing(14)

        existing_card = self._choice_card(
            "1. Usar uma pasta existente",
            "A aplicação usará os arquivos diretamente na pasta escolhida.",
        )
        self.use_folder_button = PrimaryButton("Escolher pasta…")
        self.use_folder_button.clicked.connect(self._choose_existing_folder)
        existing_card.layout().addWidget(self.use_folder_button)
        choices.addWidget(existing_card, 1)

        import_card = self._choice_card(
            "2. Importar para esta aplicação",
            "Selecione um ou mais arquivos para copiar com segurança para "
            "user_data.",
        )
        self.import_button = PrimaryButton("Selecionar arquivos…")
        self.import_button.setObjectName("orangeButton")
        self.import_button.clicked.connect(self._choose_import_files)
        import_card.layout().addWidget(self.import_button)
        choices.addWidget(import_card, 1)
        layout.addLayout(choices)

        self.status_panel = QFrame()
        self.status_panel.setObjectName("setupStatusPanel")
        status_layout = QVBoxLayout(self.status_panel)
        status_layout.setContentsMargins(16, 14, 16, 14)
        status_layout.setSpacing(6)
        status_title = QLabel("Situação de user_data")
        status_title.setObjectName("setupStatusTitle")
        self.status_label = QLabel()
        self.status_label.setObjectName("setupStatus")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_label)
        layout.addWidget(self.status_panel)

        actions = QHBoxLayout()
        self.use_managed_button = QPushButton(
            "Usar arquivos já presentes em user_data"
        )
        self.use_managed_button.setObjectName("secondaryButton")
        self.use_managed_button.clicked.connect(self._use_managed_data)
        actions.addWidget(self.use_managed_button)
        actions.addStretch(1)
        continue_button = QPushButton("Continuar sem configurar")
        continue_button.setObjectName("quietButton")
        continue_button.clicked.connect(self.reject)
        actions.addWidget(continue_button)
        layout.addLayout(actions)

        self._refresh_managed_status()

    @staticmethod
    def _choice_card(title_text: str, body_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("setupChoiceCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        title = QLabel(title_text)
        title.setObjectName("setupChoiceTitle")
        body = QLabel(body_text)
        body.setObjectName("setupChoiceBody")
        body.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(body, 1)
        return card

    def _refresh_managed_status(self) -> None:
        missing = missing_required_files(self._managed_root)
        present_count = len(REQUIRED_DATA_FILES) - len(missing)
        optional = present_optional_files(self._managed_root)
        lines = [
            f"Arquivos obrigatórios encontrados: "
            f"{present_count}/{len(REQUIRED_DATA_FILES)}."
        ]
        if missing:
            lines.append("Ainda faltam: " + ", ".join(missing) + ".")
        else:
            lines.append("Os dados locais obrigatórios estão completos.")
        if optional:
            lines.append(
                "Arquivos Google opcionais encontrados: "
                + ", ".join(optional)
                + "."
            )
        else:
            lines.append(
                "Arquivos Google são opcionais e podem ser importados depois."
            )
        self.status_label.setText("\n".join(lines))
        self.use_managed_button.setEnabled(not missing)

    def _choose_existing_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Escolha a pasta de dados do ACAMP",
        )
        if not selected:
            return
        selected_root = Path(selected)
        missing = missing_required_files(selected_root)
        if missing:
            QMessageBox.warning(
                self,
                "Pasta incompleta",
                "A pasta escolhida não contém todos os arquivos "
                "obrigatórios.\n\nFaltam: " + ", ".join(missing),
            )
            return
        if not self._store.save_external(selected_root):
            QMessageBox.warning(
                self,
                "Não foi possível salvar",
                "A localização escolhida não pôde ser salva.",
            )
            return
        self.accept()

    def _choose_import_files(self) -> None:
        selected, _filter = QFileDialog.getOpenFileNames(
            self,
            "Selecione os arquivos de dados do ACAMP",
            "",
            "Arquivos JSON (*.json)",
        )
        if not selected:
            return

        selected_paths = tuple(Path(value) for value in selected)
        result = import_runtime_files(selected_paths, self._managed_root)
        if result.failed:
            QMessageBox.warning(
                self,
                "Importação incompleta",
                "Alguns arquivos não puderam ser importados: "
                + ", ".join(result.failed),
            )
        if result.rejected:
            QMessageBox.information(
                self,
                "Arquivos ignorados",
                "Somente os arquivos reconhecidos pelo ACAMP são aceitos. "
                "Ignorados: " + ", ".join(result.rejected),
            )
        self._refresh_managed_status()

        if not missing_required_files(self._managed_root):
            if not self._store.save_managed():
                QMessageBox.warning(
                    self,
                    "Não foi possível salvar",
                    "Os arquivos foram importados, mas a configuração não "
                    "pôde ser salva.",
                )
                return
            self.accept()
        elif result.copied:
            QMessageBox.information(
                self,
                "Arquivos importados",
                "Os arquivos selecionados foram importados. Selecione os "
                "arquivos obrigatórios restantes para concluir.",
            )

    def _use_managed_data(self) -> None:
        if missing_required_files(self._managed_root):
            self._refresh_managed_status()
            return
        if not self._store.save_managed():
            QMessageBox.warning(
                self,
                "Não foi possível salvar",
                "A configuração de dados não pôde ser salva.",
            )
            return
        self.accept()
