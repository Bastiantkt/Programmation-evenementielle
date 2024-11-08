import socket
import threading
import subprocess
import sys
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Vérification des arguments
if len(sys.argv) < 4:
    print("Utilisation : python serveur_maitre.py <max_programmes> <port_maitre> <ports_secondaires>")
    print("Exemple : python serveur_maitre.py 5 8000 9001,9002,9003")
    sys.exit(1)

# Nombre maximum de programmes pour le serveur maître
MAX_PROGRAMS = int(sys.argv[1])

# Port du serveur maître
MASTER_PORT = int(sys.argv[2])

# Ports des serveurs secondaires (séparés par des virgules dans les arguments)
SECONDARY_PORTS = [int(port) for port in sys.argv[3].split(',')]
SECONDARY_SERVERS = [("127.0.0.1", port) for port in SECONDARY_PORTS]  # Adresses IP et ports des serveurs secondaires

def delegate_to_secondary(client_socket, client_address, program_size, program_data):
    logging.info(f"Tentative de délégation pour le client {client_address}")
    for server_ip, server_port in SECONDARY_SERVERS:
        try:
            secondary_socket = socket.create_connection((server_ip, server_port))
            secondary_socket.sendall(str(program_size).encode())
            if secondary_socket.recv(1024).decode() == "TAILLE_RECUE":
                logging.info(f"Délégation au serveur secondaire {server_ip}:{server_port}")
                secondary_socket.sendall(program_data)

                # Recevoir les résultats du serveur secondaire et les envoyer au client
                while True:
                    response = secondary_socket.recv(4096)
                    if not response:
                        break
                    client_socket.sendall(response)
                
                logging.info(f"Résultats reçus du serveur secondaire {server_ip}:{server_port} pour le client {client_address}")
                secondary_socket.close()
                return True
        except Exception as e:
            logging.error(f"Erreur lors de la délégation au serveur secondaire {server_ip}:{server_port} : {e}")
            continue
    logging.warning(f"Échec de la délégation pour le client {client_address}")
    return False

def handle_client(client_socket, client_address):
    filename = None  # Initialisation de la variable filename pour éviter l'UnboundLocalError

    try:
        # Recevoir la taille du programme
        data = client_socket.recv(1024).decode()
        if not data:
            logging.warning(f"Aucune donnée reçue de {client_address}, fermeture de la connexion.")
            client_socket.close()
            return
        program_size = int(data)

        client_socket.sendall("TAILLE_RECUE".encode())
        logging.info(f"Taille du programme reçue : {program_size} octets")

        # Recevoir le programme
        program_data = b''
        while len(program_data) < program_size:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            program_data += chunk

        logging.info(f"Programme reçu, taille totale : {len(program_data)} octets")

        # Vérifier si le maître peut traiter la tâche ou doit déléguer
        if threading.active_count() - 1 >= MAX_PROGRAMS:  # -1 pour exclure le thread principal
            if delegate_to_secondary(client_socket, client_address, program_size, program_data):
                logging.info(f"Tâche déléguée pour le client {client_address}")
                return
            else:
                client_socket.sendall("Impossible de déléguer la tâche.".encode())
                logging.warning(f"Délégation échouée pour le client {client_address}")
                return

        # Sauvegarder le programme dans un fichier temporaire
        filename = f"programme_client_{client_address[1]}_{threading.get_ident()}.py"
        with open(filename, "wb") as f:
            f.write(program_data)
        logging.info(f"Programme sauvegardé dans le fichier {filename}")

        # Exécuter le programme et capturer la sortie
        process = subprocess.Popen(['python', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        # Envoyer les résultats au client
        if stdout:
            client_socket.sendall(("SORTIE:\n" + stdout).encode())
            logging.info(f"Sortie du programme envoyée au client : \n{stdout}")
        if stderr:
            client_socket.sendall(("ERREURS:\n" + stderr).encode())
            logging.info(f"Erreurs du programme envoyées au client : \n{stderr}")
        if not stdout and not stderr:
            client_socket.sendall("Aucune sortie.".encode())
            logging.info("Aucune sortie du programme")

    except Exception as e:
        error_msg = f"Une erreur est survenue : {str(e)}"
        client_socket.sendall(error_msg.encode())
        logging.error(error_msg)
    finally:
        client_socket.close()
        logging.info(f"Connexion avec le client {client_address} fermée")
        
        # Supprimer le fichier temporaire seulement s'il existe
        if filename and os.path.exists(filename):
            os.remove(filename)
            logging.info(f"Fichier temporaire {filename} supprimé")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', MASTER_PORT))
    server.listen(5)
    logging.info(f"Serveur maître démarré sur le port {MASTER_PORT} avec un maximum de {MAX_PROGRAMS} programmes.")
    logging.info(f"Serveurs secondaires configurés : {SECONDARY_SERVERS}")

    try:
        while True:
            client_socket, client_address = server.accept()
            logging.info(f"Connexion acceptée du client {client_address}")

            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Arrêt du serveur maître.")
    finally:
        server.close()
        logging.info("Serveur maître arrêté.")

if __name__ == "__main__":
    main()
