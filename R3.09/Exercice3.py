import csv

class Article:
    TVA = 0.2

    def __init__(self, nom: str, code_barre: str, prix_ht: float):
        if prix_ht <= 0:
            raise ValueError("Le prix hors taxe doit être supérieur à 0.")
        self.nom = nom
        self.code_barre = code_barre
        self.prix_ht = prix_ht

    def get_nom(self):
        return self.nom

    def get_code_barre(self):
        return self.code_barre

    def get_prix_ht(self):
        return self.prix_ht

    def set_prix_ht(self, nouveau_prix_ht: float):
        if nouveau_prix_ht <= 0:
            raise ValueError("Le nouveau prix hors taxe doit être supérieur à 0.")
        self.prix_ht = nouveau_prix_ht

    def prix_ttc(self):
        return self.prix_ht * (1 + Article.TVA)


class Stock:
    def __init__(self):
        self.articles = {}

    def taille(self):
        return len(self.articles)

    def ajout(self, article: Article):
        if article.get_code_barre() in self.articles:
            raise ValueError("Un article avec ce code-barre existe déjà.")
        self.articles[article.get_code_barre()] = article

    def recherche_par_code_barre(self, code_barre: str):
        if code_barre not in self.articles:
            raise ValueError("Article non trouvé pour ce code-barre.")
        return self.articles[code_barre]

    def recherche_par_nom(self, nom: str):
        for article in self.articles.values():
            if article.get_nom() == nom:
                return article
        raise ValueError("Article non trouvé pour ce nom.")

    def supprime_par_code_barre(self, code_barre: str):
        if code_barre not in self.articles:
            raise ValueError("Article non trouvé pour ce code-barre.")
        del self.articles[code_barre]

    def supprime_par_nom(self, nom: str):
        for code, article in list(self.articles.items()):
            if article.get_nom() == nom:
                del self.articles[code]
                return
        raise ValueError("Article non trouvé pour ce nom.")

    def lire_fichier_csv(self, nom_fichier: str):
        try:
            with open(nom_fichier, mode='r', newline='', encoding='utf-8') as fichier:
                lecteur_csv = csv.reader(fichier)
                for ligne in lecteur_csv:
                    nom, code_barre, prix_ht = ligne
                    try:
                        article = Article(nom, code_barre, float(prix_ht))
                        self.ajout(article)
                    except ValueError as e:
                        print(f"Erreur : {e}")
        except FileNotFoundError:
            print("Erreur : Fichier introuvable.")
        except IOError:
            print("Erreur : Problème d'entrée/sortie.")

    def sauvegarder_fichier_csv(self, nom_fichier: str):
        try:
            with open(nom_fichier, mode='w', newline='', encoding='utf-8') as fichier:
                ecrivain_csv = csv.writer(fichier)
                for article in self.articles.values():
                    ecrivain_csv.writerow([article.get_nom(), article.get_code_barre(), article.get_prix_ht()])
        except IOError:
            print("Erreur : Problème d'entrée/sortie.")

stock = Stock()

while True:
    nom = input("Nom de l'article (ou 'q' pour quitter) : ")
    if nom.lower() == 'q':
        break
    code_barre = input("Code-barre de l'article : ")
    prix_ht = float(input("Prix hors taxe de l'article : "))
    try:
        article = Article(nom, code_barre, prix_ht)
        stock.ajout(article)
        print("Article ajouté.")
    except ValueError as e:
        print("Erreur :", e)

print("Taille du stock:", stock.taille())

stock.sauvegarder_fichier_csv("stock.csv")
