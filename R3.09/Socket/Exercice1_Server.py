import socket

server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 12345))
server_socket.listen(1)
print("Serveur en attente de connexion...")

conn, address = server_socket.accept()
print(f"Connexion de {address}")

message = conn.recv(1024).decode()
print(f"Message reçu : {message}")

reply = "Message reçu"
conn.send(reply.encode())

conn.close()
server_socket.close()
