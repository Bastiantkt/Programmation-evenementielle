import socket
import threading

clients = []

def broadcast(message, sender_socket):
    for client_socket in clients:
        if client_socket != sender_socket:
            client_socket.send(message.encode())

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if message == "bye":
                print("Client déconnecté")
                clients.remove(client_socket)
                client_socket.close()
                break
            elif message == "arret":
                print("Arrêt du serveur")
                for sock in clients:
                    sock.close()
                server_socket.close()
                exit()
            else:
                print("Message reçu :", message)
                broadcast(message, client_socket)
        except:
            break

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 3333))
server_socket.listen()

print("Serveur de discussion démarré...")

while True:
    client_socket, addr = server_socket.accept()
    clients.append(client_socket)
    print("Nouveau client connecté :", addr)
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()
