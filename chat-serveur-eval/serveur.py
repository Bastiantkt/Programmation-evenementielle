import socket
import sys
from PyQt6 import QtWidgets
from threading import Thread


class GUI_APPS(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.THREAD_SERVEUR = None  
        self.SERVEUR_EXEC = False  
        self.INIT_GUI()

    def INIT_GUI(self):
        self.setWindowTitle('Le serveur de tchat')

        self.ip_label = QtWidgets.QLabel('Serveur')
        self.ip_input = QtWidgets.QLineEdit(self)
        self.ip_input.setText('0.0.0.0')
        self.port_label = QtWidgets.QLabel('Port')
        self.port_input = QtWidgets.QLineEdit(self)
        self.port_input.setText('10000')
        self.bouton = QtWidgets.QPushButton('Démarrer le serveur', self)
        self.bouton.clicked.connect(self.__demarrage_bouton)
        self.resultat = QtWidgets.QTextEdit(self)
        self.resultat.setReadOnly(True)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.ip_label)
        grid.addWidget(self.ip_input)
        grid.addWidget(self.port_label)
        grid.addWidget(self.port_input)
        grid.addWidget(self.bouton)
        grid.addWidget(self.resultat)
        self.setLayout(grid)
        self.show()

    def __demarrage_bouton(self):
        if self.SERVEUR_EXEC:
            self.__arreter_serveur()
        else:
            self.__demarrer_serveur()

    def __demarrer_serveur(self):
        self.SERVEUR_EXEC = True
        self.THREAD_SERVEUR = Thread(target=self.__demarrage, daemon=True)
        self.THREAD_SERVEUR.start()
        self.bouton.setText("Arrêter le serveur")

    def __arreter_serveur(self):
        self.SERVEUR_EXEC = False
        self.bouton.setText("Démarrer le serveur")

    def __demarrage(self):
        IP_SERVEUR = self.ip_input.text()
        PORT_SERVEUR = int(self.port_input.text())

        SOCKET_SERVEUR = socket.socket()
        try:
            SOCKET_SERVEUR.bind((IP_SERVEUR, PORT_SERVEUR))
            SOCKET_SERVEUR.listen(5)
            while self.SERVEUR_EXEC:
                try:
                    SOCKET_SERVEUR.settimeout(1) 
                    connexion, adresse = SOCKET_SERVEUR.accept()
                    Thread(target=self.__accept, args=(connexion, adresse), daemon=True).start()
                except socket.timeout:
                    continue
        finally:
            SOCKET_SERVEUR.close()

    def __accept(self, connexion, adresse):
        while self.SERVEUR_EXEC:
            try:
                message = connexion.recv(1024).decode()
                self.mettre_a_jour_resultat(f"{adresse} : {message}")
                if message.lower() == "bye":
                    connexion.send("Au revoir.".encode())
                    self.__arreter_serveur()
                elif message.lower() == "arret":
                    connexion.send("arret".encode())
                    self.__arreter_serveur()
                reponse = "Message reçu"
                connexion.send(reponse.encode())
            except Exception as e:
                break
        connexion.close()

    def mettre_a_jour_resultat(self, message):
        self.resultat.append(message)


def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = GUI_APPS()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
