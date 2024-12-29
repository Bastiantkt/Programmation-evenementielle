🛠️ Projet : Cluster de Calcul avec du Load-Balancing

							🎥 -Démonstration- : 
	
 -[Regarder la vidéo](https://drive.google.com/file/d/1Dk7CMTXXXkSrzTFJfp3_4FYCnZOScKqN/preview)-
	

📜 -Description- :

	// Ce projet met en œuvre une architecture multi-serveurs permettant de compiler et d'exécuter des programmes soumis par des clients. Le serveur maître gère les connexions et distribue les tâches aux serveurs secondaires pour équilibrer la charge. //

-💡 Fonctionnalités- :

	* Gestion des clients multiples via une interface graphique.
	* Compilation et exécution de programmes en Python, Java, C et C++.
	* Répartition dynamique de la charge.
	* Surveillance des ressources CPU et RAM et Max Programmes.
	* Robustesse avec gestion des échecs de connexion.
	* Sécurité renforcée avec chiffrement du header via une clé partagée..

-📦 Pré-requis- :

	* Python 3.8+
	* Modules : voir requirements.txt
	* Compilateurs pour C et C++ (GCC, G++

🔧 -Installation- :

	* Clonez ce dépôt :
	
	$ cd ~
	$ git clone https://github.com/Bastiantkt/Programmation-evenementielle.git

	* Installez les dépendances :
	
	$ cd Programmation-evenementielle/SAE3.02/
	$ pip install -r requirements.txt

🚀 -Démarrage- :

	* Serveur Maître :
	
	$ cd ~
	$ cd Programmation-evenementielle/SAE3.02/SERVEUR/
	$ python3 serveur.py <port_maitre> '<ips_autres>' '<ports_autres>' <max_programmes> <max_cpu_usage> <max_ram_usage>

![Aperçu de l'application](images/screenshot1.png)
-------------------------------------------------------------------------------------------------------------------------------	
	⚠️ Example : $ python3 serveur.py 12345 '127.0.0.1,192.168.1.2' '12346,12347;12348,12349' 2 50 80

-------------------------------------------------------------------------------------------------------------------------------
	
	* Serveur Secondaire :
	
	$ cd ~
	$ cd Programmation-evenementielle/SAE3.02/SERVEUR/
	$ python3 serveur_secondaire.py <port> <max_programmes> <max_cpu_usage> <max_ram_usage>
						    
![Aperçu de l'application](images/creenshot1.png)
-------------------------------------------------------------------------------------------------------------------------------	
	⚠️ Exemple : $ python3 serveur_secondaire.py 12346 2 50 50

-------------------------------------------------------------------------------------------------------------------------------
						    
	* Client :
	
	$ cd ~
	$ cd Programmation-evenementielle/SAE3.02/CLIENT/
	$ python3 client.py

![Aperçu de l'application](images/Screenshot1.png)


	