import socket
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox

def CssLoader(filename):
    with open(filename, 'r') as rd:
        content = rd.read()
    return content

class ClientApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Client')

        # CSS
        self.setStyleSheet(CssLoader('main.css'))

        # IP Address Input
        self.ip_label = QtWidgets.QLabel('IP du serveur :')
        self.ip_input = QtWidgets.QLineEdit(self)
        self.ip_input.setText('localhost')

        # Port Input
        self.port_label = QtWidgets.QLabel('Port du serveur :')
        self.port_input = QtWidgets.QLineEdit(self)
        self.port_input.setText('12345')

        # Send Button
        self.send_button = QtWidgets.QPushButton('Envoyer le programme', self)
        self.send_button.clicked.connect(self.send_program)

        # Result Text Area
        self.result_text = QtWidgets.QTextEdit(self)
        self.result_text.setReadOnly(True)

        # Layout
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.ip_label, 1, 0)
        grid.addWidget(self.ip_input, 1, 1)

        grid.addWidget(self.port_label, 2, 0)
        grid.addWidget(self.port_input, 2, 1)

        grid.addWidget(self.send_button, 3, 0, 1, 2)

        grid.addWidget(self.result_text, 4, 0, 5, 2)

        self.setLayout(grid)

        self.show()

    def send_program(self):
        # Get server IP and port
        server_ip = self.ip_input.text()
        server_port = int(self.port_input.text())

        # Open file dialog to select the program file
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionnez le programme", "", "Fichiers Python (*.py)", options=options)
        if not file_path:
            return

        # Read the program data
        try:
            with open(file_path, "rb") as f:
                program_data = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier : {str(e)}")
            return

        # Start a new thread to send the program
        self.thread = QtCore.QThread()
        self.worker = Worker(server_ip, server_port, program_data)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.update_result.connect(self.update_result)
        self.thread.start()

        self.result_text.clear()
        self.result_text.append("En attente du résultat...\n")

    def update_result(self, data):
        self.result_text.append(data)

    def on_finished(self):
        self.thread.quit()
        self.thread.wait()

class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    update_result = QtCore.pyqtSignal(str)

    def __init__(self, server_ip, server_port, program_data):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.program_data = program_data

    def run(self):
        try:
            # Create a socket and connect to the server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_ip, self.server_port))

            # Send the size of the program
            program_size = str(len(self.program_data)).encode()
            client_socket.sendall(program_size)

            # Wait for acknowledgment
            ack = client_socket.recv(1024).decode()
            if ack != "TAILLE_RECUE":
                raise Exception("Problème lors de l'envoi de la taille du programme.")

            # Send the program
            client_socket.sendall(self.program_data)

            # Receive and display the results
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
    client_app = ClientApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
