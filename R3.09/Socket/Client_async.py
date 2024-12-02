import socket
import threading

def receive_messages(client_socket, stop_event):
    while not stop_event.is_set():
        try:
            reply = client_socket.recv(1024).decode()
            if not reply:
                break
            print(f"Serveur : {reply}")
            if reply.lower() == "arret":
                print("Le serveur a demandé l'arrêt. Fermeture du client.")
                stop_event.set()
                break
        except:
            break

def send_messages(client_socket, stop_event):
    while not stop_event.is_set():
        message = input("Client : ")
        client_socket.send(message.encode())
        if message.lower() == "arret" or "bye":
            stop_event.set()
            break

while True:
    client_socket = socket.socket()
    client_socket.connect(('localhost', 12346))
    print("Client connecté au serveur asynchrone")

    stop_event = threading.Event()

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket, stop_event))
    send_thread = threading.Thread(target=send_messages, args=(client_socket, stop_event))
    receive_thread.start()
    send_thread.start()

    receive_thread.join()
    send_thread.join()

    client_socket.close()
    print("Client déconnecté.")
    
    if stop_event.is_set():
        print("Fin du programme client.")
        break
