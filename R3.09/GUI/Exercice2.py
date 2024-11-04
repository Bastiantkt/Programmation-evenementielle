import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt

class TemperatureConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convertisseur de température")
        self.setGeometry(100, 100, 400, 200)

        self.unit_label = QLabel("Unité:")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Celsius", "Kelvin"])
        self.unit_combo.currentIndexChanged.connect(self.update_conversion)

        self.input_label = QLabel("Température:")
        self.input_temp = QLineEdit()
        self.input_temp.setPlaceholderText("Entrez une température")
        self.input_temp.textChanged.connect(self.update_conversion)

        self.result_label = QLabel("Conversion:")
        self.result_temp = QLineEdit()
        self.result_temp.setReadOnly(True)
        
        layout = QVBoxLayout()
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(self.unit_label)
        unit_layout.addWidget(self.unit_combo)
        layout.addLayout(unit_layout)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_temp)
        layout.addLayout(input_layout)

        result_layout = QHBoxLayout()
        result_layout.addWidget(self.result_label)
        result_layout.addWidget(self.result_temp)
        layout.addLayout(result_layout)

        self.setLayout(layout)

    def update_conversion(self):
        try:
            temp = float(self.input_temp.text())
            if self.unit_combo.currentText() == "Celsius":
                if temp < -273.15:
                    raise ValueError("Température sous le zéro absolu en Celsius.")
                converted = temp + 273.15
            else:
                if temp < 0:
                    raise ValueError("Température sous le zéro absolu en Kelvin.")
                converted = temp - 273.15
            self.result_temp.setText(f"{converted:.2f}")
        except ValueError as e:
            if self.input_temp.text():
                QMessageBox.critical(self, "Erreur de saisie", str(e))
                self.result_temp.clear()

app = QApplication(sys.argv)
window = TemperatureConverter()
window.show()
sys.exit(app.exec_())
