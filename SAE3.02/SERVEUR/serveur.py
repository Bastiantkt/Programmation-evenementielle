import socket
import threading
import subprocess
import sys
import os
import logging
import re
import psutil
import time
import platform
from queue import Queue



# ------------
# -CONFIGURATION LOGGING-
# ------------

logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",  
    handlers=[
        logging.StreamHandler(sys.stdout)  
    ]
)

# ------------
# -ARGUMENTS-
# ------------

if len(sys.argv) < 4:
    print("Utilisation : python3 serveur.py <port_maitre> <ips_autres> <ports_autres> <max_programmes> <max_cpu_usage> <max_ram_usage>")
    print("Exemple : python3 serveur.py 12345 127.0.0.1,192.168.1.2 12346,12347;12348,12349 2 50 80")
    sys.exit(1)

# ------------
# -ARGUMENTS MAX PROGRAMME-
# ------------

MAX_PROGRAMMES = int(sys.argv[4])

# ------------
# -ARGUMENTS UTILISATION CPU- 
# ------------

MAX_CPU_USAGE = int(sys.argv[5])

# ------------
# -ARGUMENTS UTILISATION RAM- 
# ------------

MAX_RAM_USAGE = int(sys.argv[6])

# ------------
# -ARGUMENTS PORT SERVEUR MAITRE-
# ------------

PORT_MAITRE = int(sys.argv[1])

# ------------
# -VARIABLE CLE SECRETE-
# ------------

SECRET_KEY = "cle_secrete_IUT_COLMAR"

# ------------
# -ARGUMENTS ADRESSES IP / PORT DES SERVEURS AUTRES-
# ------------

ips = sys.argv[2].split(',')
ports_groupes = sys.argv[3].split(';')

SERVEUR_AUTRES = []
for ip, ports in zip(ips, ports_groupes):
    for port in ports.split(','):
        SERVEUR_AUTRES.append((ip, int(port))) 

# ------------
# -FONCTION DELEGATION AUX AUTRES SERVEURS-
# ------------

def delegation_serveurs_autres(socket_client, adresse_client, language_code, taille_programme, programme):
    meilleur_serveur = choisir_meilleur_serveur()
    if not meilleur_serveur:
        return False

    ip_serveur, port_serveur = meilleur_serveur
    try:
        socket_autres = socket.create_connection((ip_serveur, port_serveur))
        header = f"{SECRET_KEY}:{language_code}:{taille_programme}"
        socket_autres.sendall(header.encode())

        response = socket_autres.recv(1024).decode()
        if response != "HEADER_RECUE":
            return False

        socket_autres.sendall(programme)
        while True:
            data = socket_autres.recv(4096)
            if not data:
                break
            socket_client.sendall(data)

        socket_autres.close()
        return True
    except Exception as e:
        logging.warning(f"Délégation échouée vers {ip_serveur}:{port_serveur} - {e}")
        return False



# ------------
# -FONCTION COMPILATION / EXECUTION PROGRAMME-
# ------------

def execution_programme(language_code, fichier, adresse_client, programme=None):
    try:
        systeme = platform.system()

        # ------------
        # -PYTHON-
        # ------------

        if language_code == "py":
            resultat_programme = subprocess.run(
                ['python3' if systeme != 'Windows' else 'python', fichier],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True
            )

        # ------------
        # -JAVA-
        # ------------

        elif language_code == "java":
            classname = os.path.splitext(os.path.basename(fichier))[0]
            subprocess.run(['javac', fichier], check=True)
            resultat_programme = subprocess.run(
                ['java', classname],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True
            )
            os.remove(classname + ".class")

        # ------------
        # -C-
        # ------------

        elif language_code == "c":
            executable_sortie = f"prog_{adresse_client[1] if adresse_client else 'default'}_{threading.get_ident()}"
            executable_sortie += ".exe" if systeme == 'Windows' else ""
            subprocess.run(['gcc', fichier, '-o', executable_sortie], check=True)
            resultat_programme = subprocess.run(
                [f'./{executable_sortie}' if systeme != 'Windows' else executable_sortie],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True
            )
            os.remove(executable_sortie)

        # ------------
        # -C++-
        # ------------    

        elif language_code == "cpp":
            executable_sortie = f"prog_{adresse_client[1] if adresse_client else 'default'}_{threading.get_ident()}"
            executable_sortie += ".exe" if systeme == 'Windows' else ""
            subprocess.run(['g++', fichier, '-o', executable_sortie], check=True)
            resultat_programme = subprocess.run(
                [f'./{executable_sortie}' if systeme != 'Windows' else executable_sortie],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            os.remove(executable_sortie)
        else:
            return "", f"Langage '{language_code}' non supporté."

        return resultat_programme.stdout, resultat_programme.stderr

    except subprocess.CalledProcessError as e:
        return "", f"Erreur d'exécution : {str(e)}"
    except Exception as e:
        return "", f"Erreur : {str(e)}"

# ------------
# -GESTION CLIENT / RECEPTION PROGRAMME / ENVOIE RESULTAT-
# ------------


def stauts_serveurs(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=2) as s:
            s.sendall("STATUS".encode())
            response = s.recv(1024).decode()
            parts = dict(item.split(":") for item in response.split("/"))
            charge = int(parts["CHARGE"])
            max_programmes = int(parts["MAX_PROGRAMMES"])
            return charge, max_programmes
    except Exception as e:
        logging.warning(f"Impossible de récupérer l'état du serveur {ip}:{port} - {e}")
        return float('inf'), None


def choisir_meilleur_serveur():
    charges = {}
    for ip, port in SERVEUR_AUTRES:
        charge, max_programmes = stauts_serveurs(ip, port)
        if max_programmes and charge < max_programmes:
            charges[(ip, port)] = charge
    return min(charges, key=charges.get) if charges else None

def gestion_client(socket_client, adresse_client):
    fichier = None
    try:
        header_data = socket_client.recv(1024).decode()
        secret_key, language_code, taille_programme = header_data.split(':')
        taille_programme = int(taille_programme)
        if secret_key != SECRET_KEY:
            raise ValueError("Clé secrète invalide")

        socket_client.sendall("HEADER_RECUE".encode())
        programme = reception_données(socket_client, taille_programme)
        fichier = prepare_fichier(language_code, programme, adresse_client)

        if delegation_programme():
            sauvegarde_execution(socket_client, language_code, fichier, programme)
        elif not delegation_serveurs_autres(socket_client, adresse_client, language_code, taille_programme, programme):
            request_queue.put((socket_client, adresse_client, programme, header_data))
    except Exception as e:
        envoie_erreur(socket_client, f"Erreur : {e}")
    finally:
        if socket_client.fileno() != -1:
            socket_client.close()
        if fichier:
            nettoyage(None, fichier)

request_queue = Queue()

def gestion_file_attente():
    while True:
        socket_client, adresse_client, programme, header_data = request_queue.get()
        try:
            if socket_client.fileno() == -1: 
                logging.warning(f"Socket du client {adresse_client} fermé. Retiré de la file.")
                continue

            secret_key, language_code, taille_programme = header_data.split(':')
            taille_programme = int(taille_programme)

            if delegation_programme():
                fichier = prepare_fichier(language_code, programme, adresse_client)
                sauvegarde_execution(socket_client, language_code, fichier, programme)
                logging.info(f"Client {adresse_client} exécuté localement.")
            elif delegation_serveurs_autres(socket_client, adresse_client, language_code, taille_programme, programme):
                logging.info(f"Client {adresse_client} délégué à un serveur secondaire.")
            else:
                try:
                    socket_client.sendall(b"ATTENTE") 
                    logging.info(f"Client {adresse_client} mis en attente faute de ressources.")
                except (socket.error, BrokenPipeError) as e:
                    logging.warning(f"Erreur lors de l'envoi de l'attente au client {adresse_client} : {e}")
                    continue

                time.sleep(1) 
                request_queue.put((socket_client, adresse_client, programme, header_data))  
        except Exception as e:
            logging.error(f"Erreur dans la gestion de la file d'attente pour {adresse_client} : {e}")
            envoie_erreur(socket_client, f"Erreur : {e}")
        finally:
            request_queue.task_done()


def reception_données(socket_client, taille_programme):
    programme = b''
    while len(programme) < taille_programme:
        programme += socket_client.recv(1024)
    return programme

def prepare_fichier(language_code, programme, adresse_client):
    if language_code == "java":
        match = re.search(r'public class (\w+)', programme.decode("utf-8"))
        if not match: raise ValueError("Nom de classe Java introuvable")
        return f"{match.group(1)}.java"
    return f"programme_client_{adresse_client[1]}_{threading.get_ident()}.{language_code}"

# ------------
# -GESTION DELEGATION AUX SERVEURS AUTRES-
# ------------

active_programs = 0

def delegation_programme():
    global active_programs
    return (active_programs < MAX_PROGRAMMES and psutil.cpu_percent(interval=1) < MAX_CPU_USAGE and psutil.virtual_memory().percent < MAX_RAM_USAGE)


# ------------
# -GESTION SAUVEGARDE / LANCEMENT PROGRAMME-
# ------------

def sauvegarde_execution(socket_client, language_code, fichier, programme):
    global active_programs
    active_programs += 1  
    try:
        with open(fichier, "wb") as f:
            f.write(programme)
        stdout, stderr = execution_programme(language_code, fichier, None, programme)

        if stdout:
            socket_client.sendall(f"SORTIE:\n{stdout}".encode())
        if stderr:
            socket_client.sendall(f"ERREURS:\n{stderr}".encode())
        if not stdout and not stderr:
            socket_client.sendall("Aucune sortie.".encode())
    except Exception as e:
        envoie_erreur(socket_client, f"Erreur d'exécution : {e}")
    finally:
        active_programs -= 1  
        nettoyage(socket_client, fichier)


# ------------
# -FONCTION RENVOIE DU RESULTAT-
# ------------

def envoie_sortie(socket_client, stdout, stderr):
    if stdout: socket_client.sendall(f"SORTIE:\n{stdout}".encode())
    if stderr: socket_client.sendall(f"ERREURS:\n{stderr}".encode())
    if not stdout and not stderr: socket_client.sendall("Aucune sortie.".encode())

def envoie_erreur(socket_client, message):
    if socket_client.fileno() != -1:  
        try:
            socket_client.sendall(message.encode())
        except OSError as e:
            logging.warning(f"Impossible d'envoyer une erreur au client : {e}")


# ------------
# -FONCTION NETTOYAGE FICHIER TEMPORAIRE-
# ------------

def nettoyage(socket_client, fichier):
    if socket_client and socket_client.fileno() != -1:  
        socket_client.close()
    if fichier and os.path.exists(fichier):
        os.remove(fichier)

# ------------
# -FONCTION MONITEUR CPU / RAM-
# ------------

def Moniteur_CPU_RAM():
    while True:
        CPU = psutil.cpu_percent(interval=1)
        RAM = psutil.virtual_memory().percent 
        RAM_MB = psutil.virtual_memory().used / (1024 ** 2)  
        PROGRAMMES = active_programs
        logging.info(f"Utilisation CPU : {CPU}% / {MAX_CPU_USAGE}% | Utilisation RAM : {RAM_MB:.2f} MB ({RAM}%) / {MAX_RAM_USAGE}% | Programmes en cours : {PROGRAMMES}/{MAX_PROGRAMMES}")
        time.sleep(0.5)


# ------------
# -MAIN- 
# ------------

def main():
    serveur_maitre = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur_maitre.bind(('', PORT_MAITRE))
    serveur_maitre.listen(5)
    logging.info(f"Serveur maître démarré sur le port {PORT_MAITRE} avec un maximum de {MAX_PROGRAMMES} programmes.")
    
    threading.Thread(target=gestion_file_attente, daemon=True).start()
    threading.Thread(target=Moniteur_CPU_RAM, daemon=True).start()

    try:
        while True:
            socket_client, adresse_client = serveur_maitre.accept()
            logging.info(f"Connexion acceptée du client {adresse_client}")
            threading.Thread(target=gestion_client, args=(socket_client, adresse_client)).start()
    except KeyboardInterrupt:
        logging.info("Arrêt du serveur maître.")
    finally:
        serveur_maitre.close()


if __name__ == "__main__":
    main()
