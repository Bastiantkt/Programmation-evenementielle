import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout

class SimpleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fenêtre Simple")
        self.setGeometry(100, 100, 300, 200)

        self.label = QLabel("Cliquez sur le bouton", self)
        self.button = QPushButton("OK", self)

        self.button.clicked.connect(self.on_click)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def on_click(self):
        self.label.setText("Vous avez cliqué sur OK")

app = QApplication(sys.argv)
window = SimpleWindow()
window.show()
sys.exit(app.exec_())
