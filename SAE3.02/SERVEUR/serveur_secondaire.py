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
# -----------


if len(sys.argv) < 3:
    print("Utilisation : python3 serveur_secondaire.py <port> <max_programmes> <max_cpu_usage> <max_ram_usage>")
    print("Exemple : python3 serveur_secondaire.py 12346 2 50 50")
    sys.exit(1)

# ------------
# -PORT-
# ------------

PORT = int(sys.argv[1])

# ------------
# -MAX PROGRAMME-
# ------------

MAX_PROGRAMS = int(sys.argv[2])

# ------------
# -ARGUMENTS UTILISATION CPU- 
# ------------

MAX_CPU_USAGE = int(sys.argv[3])

# ------------
# -ARGUMENTS UTILISATION RAM- 
# ------------

MAX_RAM_USAGE = int(sys.argv[4])

# ------------
# -VARIABLE CLE SECRETE-
# ------------

SECRET_KEY = "cle_secrete_IUT_COLMAR"

# ------------
# -FONCTION COMPILATION / EXECUTION PROGRAMME-
# ------------

def execution_programme(language_code, fichier, adresse_maitre, programme=None):
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
            executable_sortie = f"prog_{adresse_maitre[1] if adresse_maitre else 'default'}_{threading.get_ident()}"
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
            executable_sortie = f"prog_{adresse_maitre[1] if adresse_maitre else 'default'}_{threading.get_ident()}"
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
    # -GESTION ENVOIE / RECEPTION : FICHIER SERVEUR MAITRE-
    # ------------  

def gestion_maitre(socket_maitre, adresse_maitre):
    fichier = None
    try:
        header_data = socket_maitre.recv(1024).decode()
        if header_data == "STATUS":
            charge = threading.active_count() - 2
            status_message = f"CHARGE:{charge}/MAX_PROGRAMMES:{MAX_PROGRAMS}/MAX_CPU:{MAX_CPU_USAGE}/MAX_RAM:{MAX_RAM_USAGE}"
            socket_maitre.sendall(status_message.encode())
            socket_maitre.close()
            return

        secret_key, language_code, program_size = header_data.split(':')
        program_size = int(program_size)
        if secret_key != SECRET_KEY:
            raise ValueError("Clé secrète invalide")
        
        socket_maitre.sendall("HEADER_RECUE".encode())
        programme = reception_données(socket_maitre, program_size)
        fichier = prepare_fichier(language_code, programme, adresse_maitre)
        sauvegarde_execution(socket_maitre, language_code, fichier, programme)
    except Exception as e:
        envoie_erreur(socket_maitre, f"Erreur : {e}")
    finally:
        nettoyage(socket_maitre, fichier)

def reception_données(socket_maitre, program_size):
    programme = b''
    while len(programme) < program_size:
        programme += socket_maitre.recv(1024)
    return programme

def prepare_fichier(language_code, programme, adresse_maitre):
    if language_code == "java":
        match = re.search(r'public class (\w+)', programme.decode("utf-8"))
        if not match: raise ValueError("Nom de classe Java introuvable")
        return f"{match.group(1)}.java"
    return f"programme_client_{adresse_maitre[1]}_{threading.get_ident()}.{language_code}"

# ------------
# -GESTION SAUVEGARDE / LANCEMENT PROGRAMME-
# ------------

def sauvegarde_execution(socket_maitre, language_code, fichier, programme):
    logging.info(f"Serveur secondaire : Lancement de l'exécution du programme en {language_code}.")
    with open(fichier, "wb") as f:
        f.write(programme)
    stdout, stderr = execution_programme(language_code, fichier, adresse_maitre=None, programme=programme)

    try:
        if stdout:
            socket_maitre.sendall(f"SORTIE:\n{stdout}".encode())
        if stderr:
            socket_maitre.sendall(f"ERREURS:\n{stderr}".encode())
        if not stdout and not stderr:
            socket_maitre.sendall("Aucune sortie.".encode())
    except Exception as e:
        socket_maitre.sendall(f"Erreur d'exécution : {str(e)}".encode())
    finally:
        socket_maitre.sendall(b"FIN_DONNEES") 



# ------------
# -FONCTION RENVOIE DU RESULTAT-
# ------------

def envoie_sortie(socket_maitre, stdout, stderr):
    try:
        if stdout:
            socket_maitre.sendall(f"SORTIE:\n{stdout}".encode())
        if stderr:
            socket_maitre.sendall(f"ERREURS:\n{stderr}".encode())
        if not stdout and not stderr:
            socket_maitre.sendall("Aucune sortie.".encode())
    finally:
        socket_maitre.shutdown(socket.SHUT_WR)  
        socket_maitre.close()


def envoie_erreur(socket_maitre, message):
    socket_maitre.sendall(message.encode())

# ------------
# -FONCTION NETTOYAGE FICHIER TEMPORAIRE-
# ------------

def nettoyage(socket_maitre, fichier):
    socket_maitre.close()
    if fichier and os.path.exists(fichier): os.remove(fichier)

# ------------
# -FONCTION MONITEUR CPU / RAM-
# ------------

def Moniteur_CPU_RAM():
    while True:
        CPU = psutil.cpu_percent(interval=1)
        RAM = psutil.virtual_memory().percent 
        RAM_MB = psutil.virtual_memory().used / (1024 ** 2)  
        PROGRAMMES = threading.active_count() - 2
        logging.info(f"Utilisation CPU : {CPU}% / {MAX_CPU_USAGE}% | Utilisation RAM : {RAM_MB:.2f} MB ({RAM}%) / {MAX_RAM_USAGE}% | Programmes en cours : {PROGRAMMES}/{MAX_PROGRAMS}")
        time.sleep(0.5)

# ------------
# -MAIN-      
# ------------

def main():
    serveur_autres = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur_autres.bind(('', PORT))
    serveur_autres.listen(MAX_PROGRAMS)
    logging.info(f"Serveur secondaire démarré sur le port {PORT} avec un maximum de {MAX_PROGRAMS} programmes.")
    thread_moniteur = threading.Thread(target=Moniteur_CPU_RAM, daemon=True)
    thread_moniteur.start()

    try:
        while True:
            socket_maitre, adresse_maitre = serveur_autres.accept()
            logging.info(f"Connexion acceptée du serveur maître {adresse_maitre}")

            if (
                threading.active_count() - 2 >= MAX_PROGRAMS or psutil.cpu_percent(interval=1) >= MAX_CPU_USAGE or psutil.virtual_memory().percent >= MAX_RAM_USAGE
            ):
                warning_msg = (f"Limite atteinte : " f"{'programmes' if threading.active_count() - 2 >= MAX_PROGRAMS else 'CPU' if psutil.cpu_percent(interval=1) >= MAX_CPU_USAGE else 'RAM'}." f" Refus de la connexion."
                )
                logging.warning(warning_msg)
                socket_maitre.sendall(warning_msg.encode())
                socket_maitre.close()
                continue

            client_thread = threading.Thread(target=gestion_maitre, args=(socket_maitre, adresse_maitre))
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Arrêt du serveur secondaire.")
    finally:
        serveur_autres.close()
        logging.info("Serveur secondaire arrêté.")


if __name__ == "__main__":
    main()

