import socket

client_socket = socket.socket()
client_socket.connect(('localhost', 12345))

message = "Bonjour, serveur !"
client_socket.send(message.encode())

reply = client_socket.recv(1024).decode()
print(f"Réponse du serveur : {reply}")

client_socket.close()
