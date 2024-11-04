import socket
import threading

def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode()
            print("Message reçu :", message)
        except:
            print("Connexion terminée")
            break

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 3333))

receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

while True:
    message = input("Message (bye pour quitter) : ")
    client_socket.send(message.encode())
    if message == "bye" or message == "arret":
        break

client_socket.close()
