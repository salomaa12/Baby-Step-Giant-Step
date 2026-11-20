# -*- coding: utf-8 -*-
"""
BSGS simplifié (grands nombres + plusieurs tests à la suite).

On saisit p (modulo), g et h ; le programme affiche les pas de bébé, les pas de
géant, les intersections et x tel que g^x ≡ h (mod p).
Le programme recommence jusqu'à ce que l'utilisateur décide d'arrêter
(réponse "n" à "Faire un autre test ?", ou "q" à n'importe quelle saisie).

Grands nombres :
  * Python gère les entiers de taille quelconque, aucune limite sur p, g, h.
  * On peut saisir 10**12 + 39 ou 2**61 - 1 (forme a**b, +k ou -k).
  * Pour les grands m, les tables ne sont pas toutes affichées (début et fin
    seulement) et la recherche s'arrête à la première correspondance.
  * La mémoire est de l'ordre de racine(p) entrées : au-delà d'environ
    5 millions d'entrées (p ~ 2,5 * 10^13) le programme demande confirmation.
"""
import re
import time
from math import isqrt, gcd

LIMITE_M = 5_000_000   # au-delà : avertissement mémoire
SEUIL_DETAIL = 40      # si m <= 40 : on affiche TOUS les pas
NB_AFFICHES = 10       # sinon on affiche seulement les 10 premiers pas


class Quitter(Exception):
    """Levée quand l'utilisateur tape q pour arrêter le programme."""


def convertir(texte):
    """Convertit un texte en entier. Accepte : 1234, 1_000_000, 2**61-1, 10**12+39. Sinon None."""
    texte = texte.replace(" ", "").replace("_", "")
    try:
        return int(texte)
    except ValueError:
        pass
    forme = re.fullmatch(r"(\d+)\*\*(\d+)([+-]\d+)?", texte)
    if forme and int(forme.group(2)) <= 10000:  # limite l'exposant pour éviter un calcul interminable
        valeur = int(forme.group(1)) ** int(forme.group(2))
        if forme.group(3):
            valeur += int(forme.group(3))
        return valeur
    return None


def est_premier(n):
    """Test de Miller-Rabin (déterministe pour n < 3,3 * 10^24, très fiable au-delà)."""
    if n < 2:
        return False
    bases = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for q in bases:
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:                          # n - 1 = d * 2^s avec d impair
        d //= 2
        s += 1
    for a in bases:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False                       # témoin de non-primalité : n est composé
    return True


def factoriser(n):
    """Facteurs premiers de n par divisions successives : dictionnaire {premier: exposant}."""
    facteurs = {}
    diviseur = 2
    while diviseur * diviseur <= n:
        while n % diviseur == 0:
            facteurs[diviseur] = facteurs.get(diviseur, 0) + 1
            n //= diviseur
        diviseur += 1
    if n > 1:
        facteurs[n] = facteurs.get(n, 0) + 1
    return facteurs


def analyser_module(p):
    """
    Distingue p premier et p composé. Renvoie (N, description) où N est la borne de
    recherche : l'ordre de g divise phi(p), donc N = phi(p) est valable ; si phi(p)
    est inconnu (p composé trop grand pour être factorisé ici), on prend N = p.
    """
    if est_premier(p):
        return p - 1, (f"p = {p} est PREMIER : le groupe (Z/pZ)* a p - 1 = {p - 1} éléments, "
                       f"l'ordre de g divise {p - 1}.")
    if p <= 10**12:
        facteurs = factoriser(p)
        phi = 1
        for q, e in facteurs.items():
            phi *= (q - 1) * q ** (e - 1)
        ecriture = " × ".join(f"{q}^{e}" if e > 1 else str(q) for q, e in facteurs.items())
        return phi, (f"p = {p} est COMPOSÉ ({p} = {ecriture}) : le groupe des éléments inversibles a "
                     f"phi(p) = {phi} éléments (et non p - 1 = {p - 1}).")
    return p, (f"p = {p} est COMPOSÉ (trop grand pour être factorisé ici) : on utilise la borne N = p, "
               f"qui reste valable car l'ordre de g est inférieur à p.")


def lire_nombre(texte):
    """Demande un entier ; recommence si la saisie est invalide ; 'q' arrête le programme."""
    while True:
        saisie = input(texte).strip().lower()
        if saisie in ("q", "quit", "quitter"):
            raise Quitter
        valeur = convertir(saisie)
        if valeur is not None:
            return valeur
        print("  -> Entrée invalide : tapez un entier (ex. 1000003 ou 2**61-1), ou q pour quitter.")


def bsgs_classique(g, h, p):
    """
    BSGS classique (pgcd(g, p) = 1 exigé). Renvoie (statut, x) :
    statut = "OK", "AUCUNE" ou "ABANDON".
    Borne N : phi(p) si connu (l'ordre de g le divise), sinon p (voir analyser_module).
    """
    N, description = analyser_module(p)
    print(description)
    m = isqrt(N - 1) + 1                       # m = plafond de racine carrée de N
    detail = m <= SEUIL_DETAIL                 # petit cas : tout afficher
    print(f"N = {N}, m = ceil(sqrt(N)) = {m}")
    if m > LIMITE_M:
        print(f"ATTENTION : {m} entrées à stocker, cela demande beaucoup de mémoire et de temps.")
        if input("Continuer quand même ? [o/N] : ").strip().lower() != "o":
            return "ABANDON", None

    # --- Pas de bébé : g^j mod p pour j = 0 .. m-1 (dictionnaire valeur -> j) ---
    print("\nPAS DE BÉBÉ (j : g^j mod p)")
    debut = time.perf_counter()
    pas_de_bebe = {}
    valeur = 1 % p
    for j in range(m):
        if detail or j < NB_AFFICHES:
            print(f"  j = {j} : {valeur}")
        elif j == NB_AFFICHES:
            print("  ...")
        if valeur not in pas_de_bebe:          # on garde le plus petit j
            pas_de_bebe[valeur] = j
        derniere = (j, valeur)
        valeur = (valeur * g) % p
    if not detail:
        print(f"  j = {derniere[0]} : {derniere[1]}")
    print(f"  ({len(pas_de_bebe)} valeurs stockées, {time.perf_counter() - debut:.3f} s)")

    # --- Pas de géant : h * (g^(-m))^i mod p pour i = 0 .. m-1 ---
    inverse_gm = pow(pow(g, m, p), -1, p)      # inverse modulaire de g^m
    print(f"\ng^m mod p = {pow(g, m, p)}, inverse de g^m = {inverse_gm}")
    print("PAS DE GÉANT (i : h * (g^-m)^i mod p)")
    debut = time.perf_counter()
    solutions = []
    valeur = h
    for i in range(m):
        if detail or i < NB_AFFICHES:
            print(f"  i = {i} : {valeur}")
        elif i == NB_AFFICHES:
            print("  ...")
        if valeur in pas_de_bebe:              # intersection trouvée
            j = pas_de_bebe[valeur]
            solutions.append((i, j, valeur))
            if not detail:                     # grand nombre : on s'arrête à la première
                if i < NB_AFFICHES:            # le pas a déjà été affiché plus haut
                    print(f"      <-- correspondance avec le pas de bébé j = {j}")
                else:
                    print(f"  i = {i} : {valeur}   <-- correspondance avec le pas de bébé j = {j}")
                break
        valeur = (valeur * inverse_gm) % p
    print(f"  ({time.perf_counter() - debut:.3f} s)")

    # --- Intersections et reconstruction x = i*m + j ---
    print("\nINTERSECTIONS (valeur commune aux deux listes)")
    if not solutions:
        return "AUCUNE", None
    for i, j, valeur in solutions:
        print(f"  valeur {valeur} : i = {i}, j = {j}  ->  x = {i}*{m} + {j} = {i * m + j}")
    i, j, _ = solutions[0]                     # première intersection = plus petite solution
    return "OK", i * m + j


def bsgs_non_inversible(g, h, p):
    """
    Cas pgcd(g, p) != 1 : BSGS ÉTENDU (algorithme distinct du classique).
    On divise par le pgcd d tant que d > 1 (il faut que d divise h), puis on
    applique le BSGS classique sur le module réduit. Renvoie (statut, x).
    """
    print(f"pgcd({g}, {p}) = {gcd(g, p)} != 1 : g n'est pas inversible, le BSGS classique ne s'applique pas.")
    print("Cela ne veut PAS dire qu'il n'y a pas de solution : on utilise le BSGS étendu.\n")
    if h == 1 % p:
        return "OK", 0                         # g^0 = 1
    p_c, h_c, k, t = p, h, 1 % p, 0
    while True:
        d = gcd(g, p_c)
        if d == 1:
            break
        if h_c % d != 0:
            print(f"  d = {d} ne divise pas h = {h_c} : aucun x >= {t + 1} ne convient "
                  f"(les x <= {t} ont déjà été testés).")
            return "AUCUNE_DIV", None          # absence prouvée sans passer par les pas de géant
        h_c //= d
        p_c //= d
        t += 1
        h_c %= p_c
        k = (k * (g // d)) % p_c
        print(f"  étape {t} : d = {d} -> module {p_c}, h = {h_c}, coefficient k = {k}")
        if k % p_c == h_c % p_c:
            return "OK", t                     # x = t est solution
    h_reduit = (h_c * pow(k, -1, p_c)) % p_c
    print(f"  Reste à résoudre : {g % p_c}^y ≡ {h_reduit} (mod {p_c}), puis x = y + {t}\n")
    statut, y = bsgs_classique(g % p_c, h_reduit, p_c)
    return (statut, y + t if y is not None else None)


def traiter_un_test():
    """Un test complet : saisie, calcul, affichage, vérification."""
    p = lire_nombre("\nModulo p : ")
    g = lire_nombre("Base g : ")
    h = lire_nombre("Valeur h : ")
    if p < 2:
        print("Erreur : le modulo p doit être un entier >= 2.")
        return
    g, h = g % p, h % p                        # ramène dans [0, p[ (négatifs et valeurs >= p acceptés)
    print(f"\nProblème : trouver x tel que {g}^x ≡ {h} (mod {p})\n")
    debut = time.perf_counter()
    if gcd(g, p) == 1:
        statut, x = bsgs_classique(g, h, p)
    else:
        statut, x = bsgs_non_inversible(g, h, p)
    duree = time.perf_counter() - debut

    print("-" * 60)
    if statut == "ABANDON":
        print("Calcul abandonné.")
    elif statut in ("AUCUNE", "AUCUNE_DIV"):
        print("Aucune solution trouvée dans le domaine de recherche.")
        print(f"Aucune solution : h = {h} n'est pas une puissance de g = {g} modulo {p}.")
        if statut == "AUCUNE":
            print("Tous les pas de géant ont été vérifiés, donc aucun exposant x n'existe "
                  "(le domaine de recherche couvre au moins une période complète de g).")
        else:
            print("La divisibilité par le pgcd est impossible : aucun exposant x n'existe.")
        if gcd(g, p) == 1 and gcd(h, p) != 1:
            print(f"Raison : g est inversible mais pgcd(h, p) = {gcd(h, p)} != 1 ; "
                  "une puissance d'un élément inversible est toujours inversible.")
        elif gcd(g, p) == 1:
            print("Raison : h n'appartient pas au sous-groupe engendré par g "
                  "(g n'engendre qu'une partie des éléments inversibles).")
    else:
        print(f"x = {x}")
        if pow(g, x, p) == h:                  # vérification finale obligatoire
            print(f"Vérification : pow({g}, {x}, {p}) = {pow(g, x, p)} = h  -> OK")
        else:
            print("ERREUR : la vérification a échoué, ce résultat n'est pas valide.")
    print(f"Temps total : {duree:.3f} s")


def main():
    print("=== BSGS : résolution de g^x ≡ h (mod p) ===")
    print("(tapez q à tout moment pour quitter ; grands nombres acceptés, ex. 10**12+39)")
    try:
        while True:
            traiter_un_test()
            if input("\nFaire un autre test ? [O/n] : ").strip().lower() in ("n", "non", "q"):
                break
    except (Quitter, EOFError, KeyboardInterrupt):
        pass
    print("\nFin du programme.")


if __name__ == "__main__":
    main()
