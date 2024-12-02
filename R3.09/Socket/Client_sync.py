import socket

client_socket = socket.socket()
client_socket.connect(('localhost', 4200))
print("Client connecté au serveur synchrone")

while True:
    # Envoi du message au serveur
    message = input("Client : ")
    client_socket.send(message.encode())
    if message.lower() == "bye":
        print("Déconnexion du client.")
        break
    elif message.lower() == "arret":
        print("Arrêt du client et demande d'arrêt du serveur.")
        break

    # Réception de la réponse du serveur
    reply = client_socket.recv(1024).decode()
    print(f"Serveur : {reply}")
    if reply.lower() == "arret":
        print("Le serveur a demandé l'arrêt. Fermeture du client.")
        break

client_socket.close()
print("Client arrêté.")
