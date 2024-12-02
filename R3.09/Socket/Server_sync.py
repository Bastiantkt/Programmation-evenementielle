import socket

def handle_client(conn, address):
    print(f"Connexion de {address}")
    while True:
        try:
            message = conn.recv(1024).decode()
            if not message:
                break
            print(f"Client : {message}")
            if message.lower() == "bye":
                print(f"Le client {address} a quitté la conversation.")
                break
            elif message.lower() == "arret":
                print("Arrêt du serveur et du client.")
                conn.send("arret".encode())
                return True  # Indique au serveur de s'arrêter
            # Répondre au client
            reply = input("Serveur : ")
            conn.send(reply.encode())
            if reply.lower() == "arret":
                return True  # Arrêter le serveur si "arret" est envoyé
        except:
            break
    conn.close()
    return False  # Indique au serveur de continuer à écouter

server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 12345))
server_socket.listen(1)
print("Serveur synchrone en attente de connexions...")

while True:
    conn, address = server_socket.accept()
    should_stop = handle_client(conn, address)
    if should_stop:
        print("Arrêt complet du serveur.")
        break

server_socket.close()
print("Serveur arrêté.")
