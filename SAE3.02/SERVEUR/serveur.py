import socket
import threading
import subprocess
import sys
import os
import logging
import re
import psutil


# ------------
# CONFIGURATION LOGGING
# ------------

logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",  
    handlers=[
        logging.StreamHandler(sys.stdout)  
    ]
)

# ------------
#ARGUMENTS
# ------------

if len(sys.argv) < 3:
    print("Utilisation : python3 serveur.py <port_maitre> <ip_autres> <ports_autres> <max_programmes> <max_cpu_usage>")
    print("Exemple : python3 serveur.py 12345 / 127.0.0.1 / 12346 / 2 / 50")
    sys.exit(1)

# ------------
# ARGUMENTS MAX PROGRAMME
# ------------

MAX_PROGRAMMES = int(sys.argv[4])

# ------------
# ARGUMENTS UTILISATION CPU 
# ------------

MAX_CPU_USAGE = int(sys.argv[5])

# ------------
# ARGUMENTS PORT SERVEUR MAITRE
# ------------

PORT_MAITRE = int(sys.argv[1])

# ------------
# ARGUMENTS PORT SERVEUR AUTRES (séparés par des virgules dans les arguments)
# ------------

PORT_AUTRES = [int(port) for port in sys.argv[3].split(',')]

# ------------
# ARGUMENTS ADRESSES IP / PORT DES SERVEURS AUTRES
# ------------

SERVEUR_AUTRES = [(str(sys.argv[2]), port) for port in PORT_AUTRES]  

# ------------
# FONCTION DELEGATION AUX AUTRES SERVEURS
# ------------

def delegation_serveurs_autres(socket_client, adresse_client, language_code, taille_programme, programme):
    for ip_serveur_autres, port_serveur_autres in SERVEUR_AUTRES:
        try:
            socket_autres = socket.create_connection((ip_serveur_autres, port_serveur_autres))
            socket_autres.sendall(f"{language_code}:{taille_programme}".encode())
            if socket_autres.recv(1024).decode() == "HEADER_RECUE":
                socket_autres.sendall(programme)
                while True:
                    response = socket_autres.recv(4096)
                    if not response: break
                    socket_client.sendall(response)
                socket_autres.close()
                return True
        except: continue
    return False

# ------------
# FONCTION COMPILATION / EXECUTION PROGRAMME
# ------------

def execution_programme(language_code, fichier, adresse_client, programme=None):
    try:

    # ------------
    # PYTHON
    # ------------

        if language_code == "py":
            resultat_programme = subprocess.run(
                ['python3', fichier],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
    # ------------
    # JAVA
    # ------------

        elif language_code == "java":
            classname = os.path.splitext(os.path.basename(fichier))[0]
            subprocess.run(['javac', fichier], check=True)
            resultat_programme = subprocess.run(
                ['java', classname],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            os.remove(classname + ".class")

    # ------------
    # C
    # ------------

        elif language_code == "c":
            executable_sortie = f"prog_{adresse_client[1] if adresse_client else 'default'}_{threading.get_ident()}"
            subprocess.run(['gcc', fichier, '-o', executable_sortie], check=True)
            resultat_programme = subprocess.run(
                ['./' + executable_sortie],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            os.remove(executable_sortie)
    
    # ------------
    # C++
    # ------------    

    
        elif language_code == "cpp":
            executable_sortie = f"prog_{adresse_client[1] if adresse_client else 'default'}_{threading.get_ident()}"
            subprocess.run(['g++', fichier, '-o', executable_sortie], check=True)
            resultat_programme = subprocess.run(
                ['./' + executable_sortie],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            os.remove(executable_sortie)
        else:
            return "", f"Langage '{language_code}' non supporté."

        return resultat_programme.stdout, resultat_programme.stderr

    except subprocess.CalledProcessError as e:
        return "", f"Erreur d'exécution : {str(e)}"
    except Exception as e:
        return "", f"Erreur : {str(e)}"

# ------------
# GESTION CLIENT / RECEPTION PROGRAMME / ENVOIE RESULTAT
# ------------

def gestion_client(socket_client, adresse_client):
    try:
        header_data = socket_client.recv(1024).decode()
        if not header_data: raise ValueError("Aucune donnée reçue")
        language_code, taille_programme = header_data.split(':')
        taille_programme = int(taille_programme)
        socket_client.sendall("HEADER_RECUE".encode())
        programme = reception_données(socket_client, taille_programme)
        fichier = prepare_fichier(language_code, programme, adresse_client)
        if not delegation_programme() and delegation_serveurs_autres(socket_client, adresse_client, language_code, taille_programme, programme): return
        sauvegarde_execution(socket_client, language_code, fichier, programme)
    except Exception as e:
        envoie_erreur(socket_client, f"Erreur : {e}")
    finally:
        nettoyage(socket_client, fichier)

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
# GESTION DELEGATION AUX SERVEURS AUTRES
# ------------

def delegation_programme():
    return threading.active_count() - 1 < MAX_PROGRAMMES and psutil.cpu_percent(interval=1) < MAX_CPU_USAGE

# ------------
# GESTION SAUVEGARDE / LANCEMENT PROGRAMME
# ------------

def sauvegarde_execution(socket_maitre, language_code, fichier, programme):
    with open(fichier, "wb") as f:
        f.write(programme)
    stdout, stderr = execution_programme(language_code, fichier, adresse_client=None, programme=programme)
    envoie_sortie(socket_maitre, stdout, stderr)

# ------------
# FONCTION RENVOIE DU RESULTAT
# ------------

def envoie_sortie(socket_client, stdout, stderr):
    if stdout: socket_client.sendall(f"SORTIE:\n{stdout}".encode())
    if stderr: socket_client.sendall(f"ERREURS:\n{stderr}".encode())
    if not stdout and not stderr: socket_client.sendall("Aucune sortie.".encode())

def envoie_erreur(socket_client, message):
    socket_client.sendall(message.encode())

# ------------
# FONCTION NETTOYAGE FICHIER TEMPORAIRE
# ------------

def nettoyage(socket_client, fichier):
    socket_client.close()
    if fichier and os.path.exists(fichier): os.remove(fichier)



# ------------
# MAIN 
# ------------

def main():
    serveur_maitre = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur_maitre.bind(('', PORT_MAITRE))
    serveur_maitre.listen(5)
    logging.info(f"Serveur maître démarré sur le port {PORT_MAITRE} avec un maximum de {MAX_PROGRAMMES} programmes.")
    client_threads = []
    try:
        while True:
            socket_client, adresse_client = serveur_maitre.accept()
            logging.info(f"Connexion acceptée du client {adresse_client}")
            client_thread = threading.Thread(target=gestion_client, args=(socket_client, adresse_client))
            client_thread.start()
            client_threads.append(client_thread)
    except KeyboardInterrupt:
        logging.info("Arrêt du serveur maître. Attente de la fin des connexions clients...")
        serveur_maitre.close()
        for thread in client_threads:
            thread.join()
        logging.info("Toutes les connexions clients ont été fermées.")
    finally:
        logging.info("Serveur maître arrêté.")


if __name__ == "__main__":
    main()
