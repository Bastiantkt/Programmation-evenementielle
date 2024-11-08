import socket
import threading
import subprocess
import sys
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Vérification des arguments
if len(sys.argv) < 3:
    print("Utilisation : python serveur_secondaire.py <max_programmes> <port>")
    sys.exit(1)

# Nombre maximum de programmes à traiter
MAX_PROGRAMS = int(sys.argv[1])
port = int(sys.argv[2])

def handle_master(master_socket, master_address):
    logging.info(f"Connexion reçue du serveur maître {master_address}")
    try:
        # Recevoir la taille du programme
        data = master_socket.recv(1024).decode()
        if not data:
            logging.warning(f"Aucune donnée reçue de {master_address}, fermeture de la connexion.")
            master_socket.close()
            return
        program_size = int(data)

        master_socket.sendall("TAILLE_RECUE".encode())
        logging.info(f"Taille du programme reçue: {program_size} octets")

        # Recevoir le programme
        program_data = b''
        while len(program_data) < program_size:
            chunk = master_socket.recv(1024)
            if not chunk:
                break
            program_data += chunk

        logging.info(f"Programme reçu, taille totale: {len(program_data)} octets")

        # Sauvegarder le programme dans un fichier temporaire
        filename = f"programme_{master_address[1]}_{threading.get_ident()}.py"
        with open(filename, "wb") as f:
            f.write(program_data)
        logging.info(f"Programme sauvegardé dans le fichier {filename}")

        # Exécuter le programme et capturer la sortie
        process = subprocess.Popen(['python', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        # Envoyer les résultats au serveur maître
        if stdout:
            master_socket.sendall(("SORTIE:\n" + stdout).encode())
            logging.info(f"Sortie du programme envoyée au serveur maître: \n{stdout}")
        if stderr:
            master_socket.sendall(("ERREURS:\n" + stderr).encode())
            logging.info(f"Erreurs du programme envoyées au serveur maître: \n{stderr}")
        if not stdout and not stderr:
            master_socket.sendall("Aucune sortie.".encode())
            logging.info("Aucune sortie du programme")

    except Exception as e:
        error_msg = f"Une erreur est survenue : {str(e)}"
        master_socket.sendall(error_msg.encode())
        logging.error(error_msg)
    finally:
        master_socket.close()
        logging.info(f"Connexion avec le serveur maître {master_address} fermée")
        # Supprimer le fichier temporaire
        if os.path.exists(filename):
            os.remove(filename)
            logging.info(f"Fichier temporaire {filename} supprimé")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(MAX_PROGRAMS)
    logging.info(f"Serveur secondaire démarré sur le port {port} avec un maximum de {MAX_PROGRAMS} programmes.")

    try:
        while True:
            master_socket, master_address = server.accept()
            logging.info(f"Connexion acceptée du serveur maître {master_address}")

            # Vérifier le nombre de threads actifs pour respecter MAX_PROGRAMS
            if threading.active_count() - 1 >= MAX_PROGRAMS:  # -1 pour exclure le thread principal
                warning_msg = "Nombre maximum de programmes atteint. Refus de la connexion."
                logging.warning(warning_msg)
                master_socket.sendall(warning_msg.encode())
                master_socket.close()
                continue

            client_thread = threading.Thread(target=handle_master, args=(master_socket, master_address))
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Arrêt du serveur secondaire.")
    finally:
        server.close()
        logging.info("Serveur secondaire arrêté.")

if __name__ == "__main__":
    main()
