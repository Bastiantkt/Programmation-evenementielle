nom_fichier = "fichier.txt"  

try:
    with open(nom_fichier, 'r') as fichier:
        for ligne in fichier:
            # Affiche chaque ligne sans les caractères de retour à la ligne
            print(ligne.rstrip("\n\r"))
except FileNotFoundError:
    print("Erreur : Le fichier spécifié est introuvable.")
except IOError:
    print("Erreur : Une erreur d'entrée/sortie s'est produite lors de l'accès au fichier.")
except FileExistsError:
    print("Erreur : Le fichier existe déjà dans ce contexte d'opération.")
except PermissionError:
    print("Erreur : Vous n'avez pas les permissions nécessaires pour accéder à ce fichier.")
finally:
    print("Fin du programme.")
