import sys
import tempfile
import subprocess
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMainWindow,
    QPushButton, QTextEdit, QLabel, QScrollArea, QGroupBox,
    QFileDialog, QComboBox, QMenuBar, QMenu, QStatusBar,
    QSplitter, QTabWidget, QDialog, QLineEdit, QDialogButtonBox
)
from PyQt6.QtGui import QFont, QIcon, QAction, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, QRegularExpression

# Configuration des tutoriels en ligne
TUTORIALS_URL = "https://aka.ms/educode-tutorials"
DOCUMENTATION_URL = "https://aka.ms/educode-docs"
COMMUNITY_URL = "https://aka.ms/educode-community"


class PythonHighlighter(QSyntaxHighlighter):
    """Colorisation syntaxique pour Python"""

    def __init__(self, document):
        super().__init__(document)

        self.highlightingRules = []

        # Mots-clés
        keywords = [
            "def", "class", "return", "import", "from", "as",
            "if", "elif", "else", "for", "while", "break",
            "continue", "try", "except", "finally", "with",
            "lambda", "None", "True", "False", "and", "or", "not", "in"
        ]

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.highlightingRules.append((pattern, keyword_format))

        # Chaînes de caractères
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        self.highlightingRules.append((QRegularExpression("\".*\""), string_format))
        self.highlightingRules.append((QRegularExpression("'.*'"), string_format))

        # Commentaires
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        self.highlightingRules.append((QRegularExpression("#[^\n]*"), comment_format))

        # Nombres
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlightingRules.append((QRegularExpression("\\b[0-9]+\\b"), number_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class EduCodeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduCode - Microsoft")
        self.setMinimumSize(1400, 900)
        self.current_theme = "dark"
        self.recent_files = []
        self.max_recent_files = 5

        # Configuration de l'interface
        self.init_ui()
        self.create_menu_bar()
        self.create_status_bar()

        # Appliquer le thème
        self.apply_theme()

        # Charger les icônes
        self.setWindowIcon(QIcon("educode.ico"))

        # Historique des modifications
        self.history = []
        self.history_index = -1

    def init_ui(self):
        """Initialise l'interface utilisateur principale"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)

        # Splitter pour la sidebar et l'éditeur
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar avec commandes
        self.sidebar = self.build_sidebar()
        splitter.addWidget(self.sidebar)

        # Zone d'édition principale
        editor_tabs = QTabWidget()
        editor_tabs.setTabsClosable(True)
        editor_tabs.tabCloseRequested.connect(self.close_tab)

        # Onglet principal
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.highlighter = PythonHighlighter(self.editor.document())

        # Console intégrée
        self.console = QTextEdit()
        self.console.setFont(QFont("Consolas", 11))
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Console de sortie...")

        # Onglets
        editor_tabs.addTab(self.editor, "Script principal")
        self.editor_tabs = editor_tabs

        # Layout pour l'éditeur et la console
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(editor_tabs)
        editor_layout.addWidget(QLabel("🖥️ Console :"))
        editor_layout.addWidget(self.console)

        # Boutons d'action
        button_layout = QHBoxLayout()

        actions = [
            ("▶ Exécuter", self.run_code, "run.png"),
            ("🔍 Déboguer", self.debug_code, "debug.png"),
            ("💡 Traduire en Python", self.translate_code, "translate.png"),
            ("💾 Sauvegarder", self.save_code, "save.png"),
            ("📂 Ouvrir", self.open_code, "open.png"),
            ("🎨 Thème", self.toggle_theme, "theme.png"),
            ("📊 Visualiser", self.visualize_code, "visualize.png"),
            ("🤖 IA Assistante", self.ai_assistant, "ai.png")
        ]

        for text, func, icon in actions:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            if icon:
                btn.setIcon(QIcon(icon))
            button_layout.addWidget(btn)

        editor_layout.addLayout(button_layout)

        # Widget pour l'éditeur et la console
        editor_widget = QWidget()
        editor_widget.setLayout(editor_layout)

        splitter.addWidget(editor_widget)
        splitter.setSizes([200, 1000])

        main_layout.addWidget(splitter)

        # Configuration des raccourcis clavier
        self.setup_shortcuts()

    def create_menu_bar(self):
        """Crée la barre de menu"""
        menubar = self.menuBar()

        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")

        new_action = QAction("Nouveau", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Ouvrir", self)
        open_action.triggered.connect(self.open_code)
        file_menu.addAction(open_action)

        save_action = QAction("Sauvegarder", self)
        save_action.triggered.connect(self.save_code)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("Quitter", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Édition
        edit_menu = menubar.addMenu("Édition")

        undo_action = QAction("Annuler", self)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Rétablir", self)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Couper", self)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copier", self)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Coller", self)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        # Menu Aide
        help_menu = menubar.addMenu("Aide")

        tutorial_action = QAction("Tutoriels en ligne", self)
        tutorial_action.triggered.connect(lambda: webbrowser.open(TUTORIALS_URL))
        help_menu.addAction(tutorial_action)

        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(lambda: webbrowser.open(DOCUMENTATION_URL))
        help_menu.addAction(docs_action)

        community_action = QAction("Communauté", self)
        community_action.triggered.connect(lambda: webbrowser.open(COMMUNITY_URL))
        help_menu.addAction(community_action)

        help_menu.addSeparator()

        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        """Crée la barre de statut"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Afficher la position du curseur
        self.cursor_label = QLabel("Ligne: 1, Colonne: 1")
        status_bar.addPermanentWidget(self.cursor_label)

        # Mise à jour de la position du curseur
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)

    def update_cursor_position(self):
        """Met à jour la position du curseur dans la barre de statut"""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_label.setText(f"Ligne: {line}, Colonne: {col}")

    def setup_shortcuts(self):
        """Configure les raccourcis clavier"""
        # Exécution rapide
        run_shortcut = QAction(self)
        run_shortcut.setShortcut("F5")
        run_shortcut.triggered.connect(self.run_code)
        self.addAction(run_shortcut)

        # Sauvegarde
        save_shortcut = QAction(self)
        save_shortcut.setShortcut("Ctrl+S")
        save_shortcut.triggered.connect(self.save_code)
        self.addAction(save_shortcut)

        # Nouveau fichier
        new_shortcut = QAction(self)
        new_shortcut.setShortcut("Ctrl+N")
        new_shortcut.triggered.connect(self.new_file)
        self.addAction(new_shortcut)

        # Assistant IA
        ai_shortcut = QAction(self)
        ai_shortcut.setShortcut("F1")
        ai_shortcut.triggered.connect(self.ai_assistant)
        self.addAction(ai_shortcut)

    def build_sidebar(self):
        """Construit la sidebar avec les commandes"""
        categories = self.command_categories()
        sidebar_layout = QVBoxLayout()

        # Barre de recherche
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Rechercher des commandes...")
        search_bar.textChanged.connect(self.filter_commands)
        sidebar_layout.addWidget(search_bar)

        # Zone de défilement
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Conteneur des commandes
        commands_container = QWidget()
        commands_layout = QVBoxLayout(commands_container)

        # Création des groupes de commandes
        self.command_groups = {}
        for cat, data in categories.items():
            group_box = QGroupBox(cat)
            group_box.setStyleSheet(
                f"QGroupBox {{ background-color: {data['color']}; color: white; font-weight: bold; border-radius: 5px; padding: 5px; }}"
            )
            vbox = QVBoxLayout()

            commands = []
            for label, code in data["commands"].items():
                btn = QPushButton(label)
                btn.clicked.connect(lambda _, c=code: self.insert_command(c))
                btn.setStyleSheet("text-align: left;")
                vbox.addWidget(btn)
                commands.append(btn)

            group_box.setLayout(vbox)
            commands_layout.addWidget(group_box)
            self.command_groups[cat] = {"widget": group_box, "commands": commands}

        commands_layout.addStretch()
        scroll_area.setWidget(commands_container)

        sidebar_layout.addWidget(scroll_area)

        # Widget pour la sidebar
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setMinimumWidth(250)

        return sidebar_widget

    def filter_commands(self, text):
        """Filtre les commandes en fonction de la recherche"""
        text = text.lower()
        for cat, group_data in self.command_groups.items():
            visible = False
            for btn in group_data["commands"]:
                if text in btn.text().lower():
                    btn.show()
                    visible = True
                else:
                    btn.hide()

            group_data["widget"].setVisible(visible)

    def insert_command(self, command):
        """Insère une commande dans l'éditeur"""
        self.editor.insertPlainText(command + "\n")
        self.editor.setFocus()

    def run_code(self):
        """Exécute le code"""
        code = self.editor.toPlainText()
        py_code = self.parse_code(code)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as f:
            f.write(py_code)
            path = f.name

        self.console.clear()
        try:
            result = subprocess.run(
                [sys.executable, path],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout + result.stderr
            if result.returncode == 0:
                output += "\n✅ Code exécuté avec succès."
        except subprocess.TimeoutExpired:
            output = "⏱️ Erreur : le script a pris trop de temps."
        except Exception as e:
            output = f"❌ Erreur à l'exécution : {str(e)}"

        self.console.setPlainText(output)
        self.statusBar().showMessage("Exécution terminée", 3000)

    def debug_code(self):
        """Mode débogage simplifié"""
        code = self.editor.toPlainText()
        py_code = self.parse_code(code)

        # Ajout de points d'arrêt visuels
        debug_code = []
        for i, line in enumerate(py_code.splitlines()):
            debug_code.append(f"print('DEBUG: Ligne {i + 1} - {line.strip()[:50]}')")
            debug_code.append(line)

        debug_code = "\n".join(debug_code)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as f:
            f.write(debug_code)
            path = f.name

        self.console.clear()
        try:
            result = subprocess.run(
                [sys.executable, path],
                capture_output=True,
                text=True,
                timeout=15
            )
            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            output = "⏱️ Erreur : le script a pris trop de temps."
        except Exception as e:
            output = f"❌ Erreur à l'exécution : {str(e)}"

        self.console.setPlainText(output)
        self.statusBar().showMessage("Débogage terminé", 3000)

    def translate_code(self):
        """Traduit le code EduCode en Python"""
        code = self.editor.toPlainText()
        py_code = self.parse_code(code)

        # Créer un nouvel onglet pour la traduction
        translation_editor = QTextEdit()
        translation_editor.setFont(QFont("Consolas", 12))
        translation_editor.setPlainText(py_code)
        translation_editor.setReadOnly(True)

        tab_index = self.editor_tabs.addTab(translation_editor, "Traduction Python")
        self.editor_tabs.setCurrentIndex(tab_index)

        self.statusBar().showMessage("Traduction terminée", 3000)

    def save_code(self):
        """Sauvegarde le code"""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le code",
            "",
            "Fichiers EduCode (*.edu);;Fichiers Python (*.py);;Tous les fichiers (*)"
        )

        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())

            self.add_recent_file(path)
            self.statusBar().showMessage(f"Fichier sauvegardé: {path}", 3000)

    def open_code(self):
        """Ouvre un fichier"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un fichier",
            "",
            "Fichiers EduCode (*.edu);;Fichiers Python (*.py);;Tous les fichiers (*)"
        )

        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())

            self.add_recent_file(path)
            self.statusBar().showMessage(f"Fichier ouvert: {path}", 3000)

    def new_file(self):
        """Crée un nouveau fichier"""
        self.editor.clear()
        self.statusBar().showMessage("Nouveau fichier créé", 2000)

    def close_tab(self, index):
        """Ferme un onglet"""
        if self.editor_tabs.count() > 1:  # Ne pas fermer le dernier onglet
            self.editor_tabs.removeTab(index)

    def toggle_theme(self):
        """Bascule entre les thèmes clair et sombre"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme()
        self.statusBar().showMessage(f"Thème {self.current_theme} activé", 2000)

    def visualize_code(self):
        """Visualisation graphique du code (simplifiée)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Visualisation du code")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        # Diagramme simplifié (en réalité, il faudrait une vraie visualisation)
        diagram = QLabel("""
        <center>
            <h3>Diagramme de flux</h3>
            <p>Cette fonctionnalité afficherait une représentation visuelle du code.</p>
            <p>Dans une version complète, cela pourrait inclure :</p>
            <ul>
                <li>Un diagramme de flux</li>
                <li>Une visualisation des variables</li>
                <li>Un graphe d'exécution</li>
            </ul>
        </center>
        """)
        diagram.setWordWrap(True)

        layout.addWidget(diagram)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec()

    def ai_assistant(self):
        """Assistant IA (simulé)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Assistant IA - EduCode")
        dialog.setMinimumSize(500, 300)

        layout = QVBoxLayout()

        prompt = QLabel("""
        <p>Comment puis-je vous aider avec votre code aujourd'hui?</p>
        <p>Exemples de questions :</p>
        <ul>
            <li>Comment faire une boucle?</li>
            <li>Pourquoi mon code ne fonctionne pas?</li>
            <li>Explique-moi les fonctions</li>
        </ul>
        """)

        question = QLineEdit()
        question.setPlaceholderText("Posez votre question ici...")

        response = QTextEdit()
        response.setReadOnly(True)
        response.setPlaceholderText("La réponse de l'IA apparaîtra ici...")

        ask_button = QPushButton("Demander à l'IA")
        ask_button.clicked.connect(lambda: self.get_ai_response(question.text(), response))

        layout.addWidget(prompt)
        layout.addWidget(question)
        layout.addWidget(response)
        layout.addWidget(ask_button)

        dialog.setLayout(layout)
        dialog.exec()

    def get_ai_response(self, question, response_widget):
        """Simule une réponse de l'IA"""
        # En réalité, on pourrait intégrer avec OpenAI API ici
        responses = {
            "boucle": "Pour faire une boucle, utilisez 'répéter n fois:' ou 'tant que condition:'",
            "fonction": "Une fonction se définit avec 'fonction nom():' et s'appelle avec 'nom()'",
            "erreur": "Vérifiez la console pour les messages d'erreur. Assurez-vous que votre syntaxe est correcte.",
            "": "Veuillez poser une question spécifique pour obtenir de l'aide."
        }

        answer = responses.get(question.lower(),
                               "Je n'ai pas compris votre question. Essayez de formuler différemment.")

        response_widget.setPlainText(f"Question: {question}\n\nRéponse IA:\n{answer}")

    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        about_text = f"""
        <center>
            <h1>EduCode</h1>
            <p>Version 1.0.0</p>
            <p>Un environnement de programmation visuelle pour tout le monde</p>
            <p>Développé par Microsoft avec ❤️</p>
            <p><a href="{TUTORIALS_URL}">Tutoriels en ligne</a> | 
            <a href="{DOCUMENTATION_URL}">Documentation</a></p>
        </center>
        """

        dialog = QDialog(self)
        dialog.setWindowTitle("À propos de EduCode")
        dialog.setMinimumSize(400, 300)

        layout = QVBoxLayout()
        label = QLabel(about_text)
        label.setOpenExternalLinks(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)

        layout.addWidget(label)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec()

    def add_recent_file(self, path):
        """Ajoute un fichier à la liste des fichiers récents"""
        if path in self.recent_files:
            self.recent_files.remove(path)

        self.recent_files.insert(0, path)
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]

        # Mettre à jour le menu (non implémenté ici pour simplifier)

    def apply_theme(self):
        """Applique le thème sélectionné"""
        if self.current_theme == "dark":
            dark_palette = """
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
            QTextEdit {
                background-color: #252525;
                color: #d4d4d4;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
            QMenuBar {
                background-color: #252525;
            }
            QMenuBar::item {
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #2d2d30;
            }
            QMenu {
                background-color: #252525;
                border: 1px solid #3e3e42;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QScrollBar:vertical {
                background: #252525;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QGroupBox {
                border: 1px solid #3e3e42;
                border-radius: 5px;
                margin-top: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #3e3e42;
            }
            QTabBar::tab {
                background: #2d2d30;
                color: #d4d4d4;
                padding: 5px;
                border: 1px solid #3e3e42;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
                border-bottom: 2px solid #007acc;
            }
            """
            self.setStyleSheet(dark_palette)
        else:
            light_palette = """
            QWidget {
                background-color: #f5f5f5;
                color: #333333;
                border: none;
            }
            QTextEdit {
                background-color: white;
                color: #333333;
                selection-background-color: #b8d6f7;
                selection-color: #000000;
            }
            QMenuBar {
                background-color: #f0f0f0;
            }
            QMenuBar::item {
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #cccccc;
            }
            QMenu::item:selected {
                background-color: #d5e6f7;
            }
            QStatusBar {
                background-color: #0078d7;
                color: white;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
            }
            QTabBar::tab {
                background: #e0e0e0;
                color: #333333;
                padding: 5px;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #0078d7;
            }
            """
            self.setStyleSheet(light_palette)

    def command_categories(self):
        """Retourne les catégories de commandes"""
        return {
            "Mouvement": {"color": "#4C97FF", "commands": {
                "déplacer(x)": 'déplacer(10)',
                "tourner_droite(deg)": 'tourner_droite(15)',
                "aller_a(x, y)": 'aller_a(100, 200)',
                "rebondir_si_bord()": 'rebondir_si_bord()'}},

            "Apparence": {"color": "#9966FF", "commands": {
                "dire(message)": 'dire("Salut")',
                "penser(message)": 'penser("Hmm...")',
                "montrer()": 'montrer()',
                "cacher()": 'cacher()',
                "changer_couleur(couleur)": 'changer_couleur("rouge")'}},

            "Contrôle": {"color": "#FFAB19", "commands": {
                "répéter n fois": 'répéter 5 fois:\n    dire("Hello")',
                "si condition": 'si x > 0:\n    dire("positif")',
                "sinon si": 'sinon si x == 0:\n    dire("zéro")',
                "sinon": 'sinon:\n    dire("négatif")',
                "attendre n sec": 'attendre(1)'}},

            "Variables": {"color": "#FF8C1A", "commands": {
                "définir variable": 'variable score = 0',
                "changer var de n": 'changer score de 1',
                "mettre var à n": 'mettre score à 10',
                "incrémenter var": 'incrémenter score'}},

            "Math": {"color": "#FF6680", "commands": {
                "addition": 'variable total = 3 + 4',
                "soustraction": 'variable rest = 10 - 2',
                "multiplication": 'variable prod = 3 * 7',
                "division": 'variable div = 8 / 2',
                "modulo": 'variable mod = 10 % 3',
                "arrondi": 'variable arr = arrondi(3.6)'}},

            "Boucle": {"color": "#0FA8A2", "commands": {
                "tant que": 'tant que x < 10:\n    changer x de 1',
                "pour chaque": 'pour chaque i dans 1..10:\n    dire(i)'}},

            "Listes": {"color": "#FF61C3", "commands": {
                "créer liste": 'liste fruits = ["pomme", "banane"]',
                "ajouter à liste": 'ajouter "orange" à fruits',
                "enlever de liste": 'enlever "pomme" de fruits',
                "parcourir liste": 'répéter pour élément dans fruits:\n    dire(élément)',
                "longueur liste": 'variable nb = longueur(fruits)'}},

            "Fonctions": {"color": "#7ED957", "commands": {
                "définir fonction": 'fonction dire_bonjour():\n    dire("Bonjour!")',
                "fonction avec param": 'fonction saluer(nom):\n    dire("Bonjour " + nom)',
                "appeler fonction": 'dire_bonjour()',
                "retourner valeur": 'fonction double(x):\n    retourner x * 2'}},

            "Événements": {"color": "#FF6F59", "commands": {
                "quand drapeau cliqué": 'quand_drapeau_clique:\n    dire("C\'est parti!")',
                "quand touche pressée": 'quand_touche_pressée("espace"):\n    dire("Espace!")',
                "quand cliqué": 'quand_cliqué:\n    dire("Cliqué!")'}},

            "Son": {"color": "#9D4EDD", "commands": {
                "jouer son": 'jouer_son("son.wav")',
                "arrêter son": 'arreter_son()',
                "changer volume": 'changer_volume(50)'}},

            "Capteurs": {"color": "#00BFFF", "commands": {
                "distance": 'distance = capteur_distance()',
                "toucher": 'si toucher():\n    dire("Touché!")',
                "couleur_détectée": 'couleur = couleur_détectée()'}},

            "Contrôle avancé": {"color": "#FFA500", "commands": {
                "pause": 'pause(2)',
                "stopper": 'stopper()',
                "stopper tout": 'stopper_tout()'}},

            "IA": {"color": "#10A37F", "commands": {
                "détecter objet": 'objet = détecter_objet(image)',
                "reconnaître parole": 'texte = reconnaître_parole(audio)',
                "générer texte": 'texte = ia_générer_texte(prompt)'}}
        }

    def parse_code(self, code):
        """Traduit le code EduCode en Python"""
        lines = code.splitlines()
        python_lines = [
            "# -*- coding: utf-8 -*-",
            "# Code généré par EduCode",
            "import time",
            "import math",
            "",
        ]

        for line in lines:
            stripped = line.strip()
            indent_level = (len(line) - len(stripped)) // 4
            indent = '    ' * indent_level

            if stripped.startswith("dire("):
                python_lines.append(indent + stripped.replace("dire", "print"))
            elif stripped.startswith("penser("):
                python_lines.append(indent + f'print("💭 {stripped[7:-1]}")')
            elif stripped.startswith("répéter"):
                parts = stripped.split()
                if "pour" in parts:
                    var = parts[2]
                    lst = parts[-1].replace(":", "")
                    python_lines.append(indent + f"for {var} in {lst}:")
                elif parts[1].isdigit():
                    python_lines.append(indent + f"for _ in range({parts[1]}):")
            elif stripped.startswith("si"):
                python_lines.append(indent + f"if {stripped[3:].strip(':')}:")
            elif stripped.startswith("sinon si"):
                python_lines.append(indent + f"elif {stripped[8:].strip(':')}:")
            elif stripped.startswith("sinon"):
                python_lines.append(indent + "else:")
            elif stripped.startswith("attendre("):
                python_lines.append(indent + f"time.sleep({stripped[8:-1]})")
            elif stripped.startswith("variable"):
                python_lines.append(indent + stripped.replace("variable", "").strip())
            elif stripped.startswith("changer"):
                var, val = stripped.split()[1], stripped.split()[3]
                python_lines.append(indent + f"{var} += {val}")
            elif stripped.startswith("incrémenter"):
                var = stripped.split()[1]
                python_lines.append(indent + f"{var} += 1")
            elif stripped.startswith("mettre"):
                var, val = stripped.split()[1], stripped.split()[3]
                python_lines.append(indent + f"{var} = {val}")
            elif stripped.startswith("tant que"):
                python_lines.append(indent + f"while {stripped[9:].strip(':')}:")
            elif stripped.startswith("ajouter"):
                el, lst = stripped.split(" à ")
                python_lines.append(indent + f"{lst}.append({el.replace('ajouter', '').strip()})")
            elif stripped.startswith("enlever"):
                el, lst = stripped.split(" de ")
                python_lines.append(indent + f"{lst}.remove({el.replace('enlever', '').strip()})")
            elif stripped.startswith("liste"):
                python_lines.append(indent + stripped.replace("liste", "").strip())
            elif stripped.startswith("fonction"):
                python_lines.append(indent + "def " + stripped.replace("fonction", "").strip())
            elif stripped.startswith("retourner"):
                python_lines.append(indent + "return " + stripped.replace("retourner", "").strip())
            elif stripped.startswith("quand_drapeau_clique"):
                python_lines.extend([
                    "",
                    indent + "if __name__ == '__main__':",
                    indent + "    main()"
                ])
            elif stripped.startswith("pause("):
                python_lines.append(indent + f"time.sleep({stripped[6:-1]})")
            elif stripped.startswith("stopper()"):
                python_lines.append(indent + "exit()")
            elif stripped.startswith("stopper_tout()"):
                python_lines.append(indent + "os._exit(0)")
            elif stripped.startswith("déplacer("):
                python_lines.append(indent + f"print('Déplacement de {stripped[8:-1]} unités')")
            elif stripped.startswith("tourner_droite("):
                python_lines.append(indent + f"print('Rotation droite de {stripped[15:-1]} degrés')")
            elif stripped.startswith("aller_a("):
                x, y = stripped[8:-1].split(",")
                python_lines.append(indent + f"print('Aller à position ({x.strip()}, {y.strip()})')")
            elif stripped.startswith("rebondir_si_bord()"):
                python_lines.append(indent + "print('Rebond si bord détecté')")
            elif stripped.startswith("montrer()"):
                python_lines.append(indent + "print('Objet visible')")
            elif stripped.startswith("cacher()"):
                python_lines.append(indent + "print('Objet caché')")
            elif stripped.startswith("changer_couleur("):
                python_lines.append(indent + f"print('Changement couleur en {stripped[16:-1]}')")
            elif stripped.startswith("jouer_son("):
                python_lines.append(indent + f"print('Jouer son {stripped[10:-1]}')")
            elif stripped.startswith("arreter_son()"):
                python_lines.append(indent + "print('Arrêt son')")
            elif stripped.startswith("changer_volume("):
                python_lines.append(indent + f"print('Volume changé à {stripped[15:-1]}')")
            elif stripped.startswith("capteur_distance()"):
                python_lines.append(indent + "distance = 0  # Valeur simulée")
            elif stripped.startswith("toucher()"):
                python_lines.append(indent + "toucher = False  # Valeur simulée")
            elif stripped.startswith("couleur_détectée()"):
                python_lines.append(indent + "couleur = 'rouge'  # Valeur simulée")
            elif stripped.startswith("détecter_objet("):
                python_lines.append(indent + f"print('Détection objet dans {stripped[15:-1]}')")
            elif stripped.startswith("reconnaître_parole("):
                python_lines.append(indent + f"print('Reconnaissance parole dans {stripped[18:-1]}')")
            elif stripped.startswith("ia_générer_texte("):
                python_lines.append(indent + f"print('Génération texte pour {stripped[17:-1]}')")
            elif stripped.startswith("pour chaque"):
                var, range_part = stripped[12:].split(" dans ")
                start, end = range_part.replace(":", "").split("..")
                python_lines.append(indent + f"for {var} in range({start}, {end}+1):")
            elif stripped.startswith("longueur("):
                python_lines.append(indent + f"len({stripped[9:-1]})")
            elif stripped.startswith("arrondi("):
                python_lines.append(indent + f"round({stripped[8:-1]})")
            elif stripped.startswith("quand_touche_pressée("):
                key = stripped[20:-2]
                python_lines.append(indent + f"# Événement touche {key} pressée")
            elif stripped.startswith("quand_cliqué"):
                python_lines.append(indent + "# Événement clic souris")
            else:
                python_lines.append(indent + stripped)

        return "\n".join(python_lines)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Style moderne
    app.setStyle("Fusion")

    window = EduCodeApp()
    window.show()
    sys.exit(app.exec())