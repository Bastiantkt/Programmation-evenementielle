import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QLineEdit

class SimpleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Une première fenêtre")
        self.setGeometry(100, 100, 300, 200)

        self.label = QLabel("Saisir votre nom", self)
        self.text_input = QLineEdit(self)
        self.button = QPushButton("OK", self)
        self.quit_button = QPushButton("Quitter", self)
        self.result_label = QLabel("", self)

        self.button.clicked.connect(self.on_click)
        self.quit_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.text_input)
        layout.addWidget(self.button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.quit_button)
        self.setLayout(layout)

    def on_click(self):
        name = self.text_input.text()
        self.result_label.setText(f"Bonjour, {name}")

app = QApplication(sys.argv)
window = SimpleWindow()
window.show()
sys.exit(app.exec_())
