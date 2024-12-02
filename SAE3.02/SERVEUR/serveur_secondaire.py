import socket
import threading
import subprocess
import sys
import os
import logging
import re

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
# -----------


if len(sys.argv) < 3:
    print("Utilisation : python3 serveur_secondaire.py <max_programmes> <port>")
    print("Exemple : python3 serveur_secondaire.py 2 12346")
    sys.exit(1)

# ------------
# MAX PROGRAMME
# ------------

MAX_PROGRAMS = int(sys.argv[1])

# ------------
# PORT
# ------------

PORT = int(sys.argv[2])

# ------------
# FONCTION COMPILATION / EXECUTION PROGRAMME
# ------------

def execution_programme(language_code, nomdufichier, adresse_maitre, programme=None):
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
        if not programme: return "Programme Manquant"
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
        executable_sortie = f"prog_{adresse_maitre[1] if adresse_maitre else 'default'}_{threading.get_ident()}"
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
        executable_sortie = f"prog_{adresse_maitre[1] if adresse_maitre else 'default'}_{threading.get_ident()}"
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
    # GESTION ENVOIE / RECEPTION : FICHIER SERVEUR MAITRE
    # ------------  

def gestion_maitre(socket_maitre, adresse_maitre):
    try:
        header_data = socket_maitre.recv(1024).decode()
        if not header_data: raise ValueError("Aucune donnée reçue")
        language_code, program_size = header_data.split(':')
        program_size = int(program_size)
        socket_maitre.sendall("HEADER_RECUE".encode())
        programme = reception_data(socket_maitre, program_size)
        nomdufichier = prepare_nomdufichier(language_code, programme, adresse_maitre)
        sauvegarde_execution(socket_maitre, language_code, nomdufichier, programme)
    except Exception as e:
        envoie_erreur(socket_maitre, f"Erreur : {e}")
    finally:
        nettoyage(socket_maitre, nomdufichier)

def reception_data(socket_maitre, program_size):
    programme = b''
    while len(programme) < program_size:
        programme += socket_maitre.recv(1024)
    return programme

def prepare_nomdufichier(language_code, programme, adresse_maitre):
    if language_code == "java":
        match = re.search(r'public class (\w+)', programme.decode("utf-8"))
        if not match: raise ValueError("Nom de classe Java introuvable")
        return f"{match.group(1)}.java"
    return f"programme_client_{adresse_maitre[1]}_{threading.get_ident()}.{language_code}"

# ------------
# GESTION SAUVEGARDE / LANCEMENT PROGRAMME
# ------------

def sauvegarde_execution(socket_maitre, language_code, nomdufichier, programme):
    with open(nomdufichier, "wb") as f:
        f.write(programme)
    stdout, stderr = execution_programme(language_code, nomdufichier, adresse_maitre=None, programme=programme)
    envoie_sortie(socket_maitre, stdout, stderr)

# ------------
# FONCTION RENVOIE DU RESULTAT
# ------------

def envoie_sortie(socket_maitre, stdout, stderr):
    if stdout: socket_maitre.sendall(f"SORTIE:\n{stdout}".encode())
    if stderr: socket_maitre.sendall(f"ERREURS:\n{stderr}".encode())
    if not stdout and not stderr: socket_maitre.sendall("Aucune sortie.".encode())

def envoie_erreur(socket_maitre, message):
    socket_maitre.sendall(message.encode())

# ------------
# FONCTION NETTOYAGE FICHIER TEMPORAIRE
# ------------

def nettoyage(socket_maitre, nomdufichier):
    socket_maitre.close()
    if nomdufichier and os.path.exists(nomdufichier): os.remove(nomdufichier)

# ------------
# MAIN 
# ------------

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT))
    server.listen(MAX_PROGRAMS)
    logging.info(f"Serveur secondaire démarré sur le port {PORT} avec un maximum de {MAX_PROGRAMS} programmes.")

    try:
        while True:
            socket_maitre, adresse_maitre = server.accept()
            logging.info(f"Connexion acceptée du serveur maître {adresse_maitre}")

            if threading.active_count() - 1 >= MAX_PROGRAMS:  
                warning_msg = "Nombre maximum de programmes atteint. Refus de la connexion."
                logging.warning(warning_msg)
                socket_maitre.sendall(warning_msg.encode())
                socket_maitre.close()
                continue

            client_thread = threading.Thread(target=gestion_maitre, args=(socket_maitre, adresse_maitre))
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Arrêt du serveur secondaire.")
    finally:
        server.close()
        logging.info("Serveur secondaire arrêté.")

if __name__ == "__main__":
    main()
