import socket
import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QFileDialog, QMessageBox

def ChargerLeCSS(fichier):
    with open(fichier, 'r') as rd:
        content = rd.read()
    return content

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
        self.ip_input = QtWidgets.QLineEdit(self)
        self.Ombre(self.ip_input)
        self.ip_input.setText('localhost')
        self.port_label = QtWidgets.QLabel('Port du serveur maitre :')
        self.port_input = QtWidgets.QLineEdit(self)
        self.Ombre(self.port_input)
        self.port_input.setText('12345')
        self.envoie_button = QtWidgets.QPushButton('Envoyer le programme', self)
        self.envoie_button.clicked.connect(self.Envoie_Programme)
        self.Ombre(self.envoie_button)
        self.resultat_text = QtWidgets.QTextEdit(self)
        self.resultat_text.setReadOnly(True)
        self.Ombre(self.resultat_text)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(15)
        grid.addWidget(self.ip_label, 1, 0)
        grid.addWidget(self.ip_input, 1, 1)
        grid.addWidget(self.port_label, 2, 0)
        grid.addWidget(self.port_input, 2, 1)
        grid.addWidget(self.envoie_button, 3, 0, 1, 2)
        grid.addWidget(self.resultat_text, 4, 0, 5, 2)
        self.setLayout(grid)
        self.show()

    def Ombre(self, widget):
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(3, 3)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        widget.setGraphicsEffect(shadow)

    def Envoie_Programme(self):
        self.envoie_button.setEnabled(False)

        ip_serveur = self.ip_input.text()
        port_serveur = int(self.port_input.text())

        options = QFileDialog.Option.DontUseNativeDialog
        chemin_fichier, _ = QFileDialog.getOpenFileName(self, "Sélectionnez le programme", "", "Tous les fichiers (*)", options=options)
        if not chemin_fichier:
            self.envoie_button.setEnabled(True)
            return

        try:
            with open(chemin_fichier, "rb") as f:
                programme = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier : {str(e)}")
            self.envoie_button.setEnabled(True)
            return

        import os
        _, extension_fichier = os.path.splitext(chemin_fichier)
        language_code = extension_fichier.lower().strip('.')

        self.thread = QtCore.QThread()
        self.worker = Worker(ip_serveur, port_serveur, programme, language_code)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.arret)
        self.worker.mettre_a_jour_resultat.connect(self.mettre_a_jour_resultat)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.resultat_text.clear()
        self.resultat_text.append("En attente du résultat...\n")

    def mettre_a_jour_resultat(self, data):
        self.resultat_text.append(data)

    def arret(self):
        self.envoie_button.setEnabled(True)
        self.thread.quit()
        self.thread.wait()
        self.thread = None
        self.worker = None


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    mettre_a_jour_resultat = QtCore.pyqtSignal(str)

    def __init__(self, ip_serveur, port_serveur, programme, language_code):
        super().__init__()
        self.ip_serveur = ip_serveur
        self.port_serveur = port_serveur
        self.programme = programme
        self.language_code = language_code

    def run(self):
        try:
            socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_client.connect((self.ip_serveur, self.port_serveur))

            header = f"{self.language_code}:{len(self.programme)}".encode()
            socket_client.sendall(header)

            ack = socket_client.recv(1024).decode()
            if ack != "HEADER_RECUE":
                raise Exception("Problème lors de l'envoi de l'en-tête.")

            socket_client.sendall(self.programme)

            result = b''
            while True:
                data = socket_client.recv(1024)
                if not data:
                    break
                result += data

            self.mettre_a_jour_resultat.emit(result.decode())
            socket_client.close()

        except Exception as e:
            message_erreur = f"Une erreur est survenue : {str(e)}"
            self.mettre_a_jour_resultat.emit(message_erreur)

        self.finished.emit()


def main():
    app = QtWidgets.QApplication(sys.argv)
    client = Interface_Application()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
