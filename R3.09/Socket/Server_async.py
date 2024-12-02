import socket
import threading

def handle_client(conn, address):
    stop_event = threading.Event()

    def receive_messages():
        while not stop_event.is_set():
            try:
                message = conn.recv(1024).decode()
                if not message:
                    break
                if message.lower() == "bye":
                    print(f"Le client {address} a quitté la conversation.")
                    break
                elif message.lower() == "arret":
                    print("Arrêt du serveur et du client.")
                    stop_event.set()
                    conn.send("arret".encode())
                    break
                print(f"Client {address} : {message}")
            except:
                break

    def send_messages():
        while not stop_event.is_set():
            reply = input("Serveur : ")
            conn.send(reply.encode())
            if reply.lower() == "arret":
                stop_event.set()
                conn.send("arret".encode())
                break

    receive_thread = threading.Thread(target=receive_messages)
    send_thread = threading.Thread(target=send_messages)
    receive_thread.start()
    send_thread.start()

    receive_thread.join()
    send_thread.join()
    conn.close()
    print(f"Connexion avec le client {address} fermée.")

server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 12346))
server_socket.listen(1)
print("Serveur asynchrone en attente de connexions...")

while True:
    conn, address = server_socket.accept()
    print(f"Connexion de {address}")
    
    client_thread = threading.Thread(target=handle_client, args=(conn, address))
    client_thread.start()
    
    client_thread.join()
    if not client_thread.is_alive():  
        print("Arrêt complet du serveur.")
        break

server_socket.close()
