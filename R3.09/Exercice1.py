def divEntier(x: int, y: int) -> int:
    if y == 0:
        raise ZeroDivisionError("Erreur : y ne peut pas être 0.")
    if x < 0 or y < 0:
        raise ValueError("Erreur : les nombres doivent être positifs.")
    
    if x < y:
        return 0
    else:
        x = x - y
        return divEntier(x, y) + 1

def main():
    try:
        x = int(input("Entrez la valeur de x (entier positif) : "))
        y = int(input("Entrez la valeur de y (entier positif) : "))
        result = divEntier(x, y)
        print(f"Le résultat de la division entière de {x} par {y} est : {result}")
    except ValueError:
        print("Erreur : Veuillez entrer des entiers positifs uniquement.")
    except ZeroDivisionError as e:
        print(e)

if __name__ == "__main__":
    main()
