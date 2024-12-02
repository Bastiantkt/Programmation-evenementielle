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

def delegate_to_others(socket_client, adresse_client, language_code, taille_programme, programme):
    for server_ip, server_port in SERVEUR_AUTRES:
        try:
            others_socket = socket.create_connection((server_ip, server_port))
            others_socket.sendall(f"{language_code}:{taille_programme}".encode())
            if others_socket.recv(1024).decode() == "HEADER_RECUE":
                others_socket.sendall(programme)
                while True:
                    response = others_socket.recv(4096)
                    if not response: break
                    socket_client.sendall(response)
                others_socket.close()
                return True
        except: continue
    return False

# ------------
# FONCTION COMPILATION / EXECUTION PROGRAMME
# ------------

def execution_programme(language_code, nomdufichier, adresse_client, programme=None):
    stdout, stderr = "", ""

    # ------------
    # PYTHON
    # ------------

    if language_code == "py":
        execution = subprocess.Popen(['python3', nomdufichier], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = execution.communicate()

    # ------------
    # JAVA
    # ------------

    elif language_code == "java":
        if not programme: return "", "Program data is missing."
        compilation = subprocess.Popen(['javac', nomdufichier], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        compile_stdout, compile_stderr = compilation.communicate()
        stderr += compile_stderr
        if not compile_stderr:
            classname = os.path.splitext(os.path.basename(nomdufichier))[0]
            execution = subprocess.Popen(['java', classname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, exec_stderr = execution.communicate()
            stderr += exec_stderr
            os.remove(classname + ".class")

    # ------------
    # C
    # ------------

    elif language_code == "c":
        executable_sortie = f"prog_{adresse_client[1] if adresse_client else 'default'}_{threading.get_ident()}"
        compilation = subprocess.Popen(['gcc', nomdufichier, '-o', executable_sortie], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        compile_stdout, compile_stderr = compilation.communicate()
        stderr += compile_stderr
        if not compile_stderr:
            execution = subprocess.Popen(['./' + executable_sortie], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, exec_stderr = execution.communicate()
            stderr += exec_stderr
            os.remove(executable_sortie)
    
    # ------------
    # C++
    # ------------    

    
    elif language_code == "cpp":
        executable_sortie = f"prog_{adresse_client[1] if adresse_client else 'default'}_{threading.get_ident()}"
        compilation = subprocess.Popen(['g++', nomdufichier, '-o', executable_sortie], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        compile_stdout, compile_stderr = compilation.communicate()
        stderr += compile_stderr
        if not compile_stderr:
            execution = subprocess.Popen(['./' + executable_sortie], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, exec_stderr = execution.communicate()
            stderr += exec_stderr
            os.remove(executable_sortie)
    else:
        stderr = f"Langage '{language_code}' non supporté."
    return stdout, stderr

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
        programme = reception_data(socket_client, taille_programme)
        nomdufichier = prepare_nomdufichier(language_code, programme, adresse_client)
        if not delegation_programme() and delegate_to_others(socket_client, adresse_client, language_code, taille_programme, programme): return
        sauvegarde_execution(socket_client, language_code, nomdufichier, programme)
    except Exception as e:
        envoie_erreur(socket_client, f"Erreur : {e}")
    finally:
        nettoyage(socket_client, nomdufichier)

def reception_data(socket_client, taille_programme):
    programme = b''
    while len(programme) < taille_programme:
        programme += socket_client.recv(1024)
    return programme

def prepare_nomdufichier(language_code, programme, adresse_client):
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

def sauvegarde_execution(socket_maitre, language_code, nomdufichier, programme):
    with open(nomdufichier, "wb") as f:
        f.write(programme)
    stdout, stderr = execution_programme(language_code, nomdufichier, adresse_client=None, programme=programme)
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

def nettoyage(socket_client, nomdufichier):
    socket_client.close()
    if nomdufichier and os.path.exists(nomdufichier): os.remove(nomdufichier)



# ------------
# MAIN 
# ------------

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT_MAITRE))
    server.listen(5)
    logging.info(f"Serveur maître démarré sur le port {PORT_MAITRE} avec un maximum de {MAX_PROGRAMMES} programmes.")
    client_threads = []
    try:
        while True:
            socket_client, adresse_client = server.accept()
            logging.info(f"Connexion acceptée du client {adresse_client}")
            client_thread = threading.Thread(target=gestion_client, args=(socket_client, adresse_client))
            client_thread.start()
            client_threads.append(client_thread)
    except KeyboardInterrupt:
        logging.info("Arrêt du serveur maître. Attente de la fin des connexions clients...")
        server.close()
        for thread in client_threads:
            thread.join()
        logging.info("Toutes les connexions clients ont été fermées.")
    finally:
        logging.info("Serveur maître arrêté.")


if __name__ == "__main__":
    main()
