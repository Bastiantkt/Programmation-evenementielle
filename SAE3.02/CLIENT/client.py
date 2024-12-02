import socket
import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QFileDialog, QMessageBox

def ChargerLeCSS(filename):
    with open(filename, 'r') as rd:
        content = rd.read()
    return content

class ShadowLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Interface_Application(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.thread = None 
        self.worker = None 

    def init_ui(self):
        self.setWindowTitle('SAE3.02')
        self.setStyleSheet(ChargerLeCSS('main.css'))
        self.ip_label = QtWidgets.QLabel('IP du serveur maitre :')
        self.ip_input = ShadowLineEdit(self)
        self.Ombre(self.ip_input)
        self.ip_input.setText('localhost')
        self.port_label = QtWidgets.QLabel('Port du serveur maitre :')
        self.port_input = ShadowLineEdit(self)
        self.Ombre(self.port_input)
        self.port_input.setText('12345')
        self.send_button = QtWidgets.QPushButton('Envoyer le programme', self)
        self.send_button.clicked.connect(self.Envoie_Programme)
        self.Ombre(self.send_button)
        self.result_text = QtWidgets.QTextEdit(self)
        self.result_text.setReadOnly(True)
        self.Ombre(self.result_text)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(15)
        grid.addWidget(self.ip_label, 1, 0)
        grid.addWidget(self.ip_input, 1, 1)
        grid.addWidget(self.port_label, 2, 0)
        grid.addWidget(self.port_input, 2, 1)
        grid.addWidget(self.send_button, 3, 0, 1, 2)
        grid.addWidget(self.result_text, 4, 0, 5, 2)
        self.setLayout(grid)
        self.show()

    def Ombre(self, widget):
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(3, 3)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        widget.setGraphicsEffect(shadow)

    def Envoie_Programme(self):
        self.send_button.setEnabled(False)

        server_ip = self.ip_input.text()
        server_port = int(self.port_input.text())

        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez le programme", "", "Tous les fichiers (*)", options=options)
        if not file_path:
            self.send_button.setEnabled(True)
            return

        try:
            with open(file_path, "rb") as f:
                program_data = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier : {str(e)}")
            self.send_button.setEnabled(True)
            return

        import os
        _, file_extension = os.path.splitext(file_path)
        language_code = file_extension.lower().strip('.')

        self.thread = QtCore.QThread()
        self.worker = Worker(server_ip, server_port, program_data, language_code)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.update_result.connect(self.update_result)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.result_text.clear()
        self.result_text.append("En attente du résultat...\n")

    def update_result(self, data):
        self.result_text.append(data)

    def on_finished(self):
        self.send_button.setEnabled(True)
        self.thread.quit()
        self.thread.wait()
        self.thread = None
        self.worker = None


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    update_result = QtCore.pyqtSignal(str)

    def __init__(self, server_ip, server_port, program_data, language_code):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.program_data = program_data
        self.language_code = language_code

    def run(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_ip, self.server_port))

            header = f"{self.language_code}:{len(self.program_data)}".encode()
            client_socket.sendall(header)

            ack = client_socket.recv(1024).decode()
            if ack != "HEADER_RECUE":
                raise Exception("Problème lors de l'envoi de l'en-tête.")

            client_socket.sendall(self.program_data)

            result = b''
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                result += data

            self.update_result.emit(result.decode())
            client_socket.close()

        except Exception as e:
            error_message = f"Une erreur est survenue : {str(e)}"
            self.update_result.emit(error_message)

        self.finished.emit()


def main():
    app = QtWidgets.QApplication(sys.argv)
    client = Interface_Application()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
