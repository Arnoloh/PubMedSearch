*Read this in [English](README.md).*

# PubMed Search

Une petite application de bureau pour chercher sur
[PubMed](https://pubmed.ncbi.nlm.nih.gov/) avec plusieurs mots-clés combinés par
`AND` / `OR` / `NOT`, et exporter les résultats vers Excel ou CSV - une ligne par
article, avec son **titre**, son **PMID**, son **DOI** et son **lien**.

Elle a été écrite pour un ami en thèse de kinésiologie : il avait des centaines
d'articles à dépouiller et lui fallait les quatre mêmes champs pour chacun.
Le faire à la main, article par article, était la partie pénible - ceci le fait
en une seule passe.

## Sommaire

- [Installation](#installation)
- [Fonctionnalités](#fonctionnalités)
- [Comment l'utiliser](#comment-lutiliser)
- [Bon à savoir](#bon-à-savoir)
- [Retours et contributions](#retours-et-contributions)

## Installation

Téléchargez `PubMedSearch.exe` depuis la
[dernière version](https://github.com/Arnoloh/PubMedSearch/releases/latest) et
lancez-le. Rien à installer : c'est un fichier unique, et il fonctionne sous
Windows.

L'application vérifie au démarrage s'il existe une version plus récente, et
propose d'ouvrir la page de téléchargement le cas échéant. Son numéro de version
est affiché en bas à droite de la fenêtre.

> L'interface de l'application est en anglais ; les noms des boutons cités
> ci-dessous sont ceux que vous verrez à l'écran.

## Fonctionnalités

**Construire la recherche**

- Autant de mots-clés que nécessaire, chacun relié aux précédents par `AND`, `OR`
  ou `NOT`.
- `+ Add keyword` ajoute une ligne, `✕` en supprime une.
- Le champ `Query`, en lecture seule, affiche exactement ce qui sera envoyé à
  PubMed, mis à jour au fil de la frappe.
- `Recent searches` conserve les 20 dernières recherches, d'une session à
  l'autre. En choisir une remplit à nouveau le formulaire : vous pouvez
  l'ajuster et la relancer.
- La touche `Entrée`, depuis n'importe où dans la fenêtre, lance la recherche.

**Lancer la recherche**

- `Limit results to` est décoché par défaut : tous les articles correspondants
  sont récupérés. Cochez-le pour vous arrêter plus tôt.
- Une barre de progression et un compteur en direct
  (`Fetching articles… 400 of 1,200`) pendant la recherche.
- Le bouton `Search` devient `Stop`. Arrêter conserve tout ce qui a déjà été
  récupéré - vous pouvez toujours l'exporter.
- La barre d'état indique combien d'articles correspondent et combien ont été
  récupérés.

**Les résultats**

- Un tableau avec le **titre**, le **PMID**, le **DOI** et le **lien** de chaque
  article.
- Double-cliquez sur une ligne pour ouvrir l'article dans votre navigateur.
- Faites glisser le bord d'une colonne pour la redimensionner, ou utilisez
  `Fit to content` / `Reset widths`.
- Les titres contenant de l'italique - noms de gènes et d'espèces, omniprésents
  sur PubMed - sont affichés en entier, et non coupés au premier mot en italique.

**Exporter**

- `Export…` enregistre les résultats. Le type de fichier suit le nom que vous
  donnez.
- `.xlsx` produit un vrai classeur Excel : liens cliquables, en-tête en gras qui
  reste visible pendant le défilement, colonnes déjà dimensionnées.
- `.csv` produit un CSV simple qu'Excel ouvre avec les accents intacts.

## Comment l'utiliser

1. **Tapez vos mots-clés.** Un par ligne, en choisissant `AND`, `OR` ou `NOT`
   pour chaque ligne après la première.
2. **Vérifiez la requête.** Le champ `Query` montre ce qui sera envoyé à PubMed :
   rien n'est deviné à votre place.
3. **Cherchez.** Appuyez sur `Search` ou sur `Entrée`.
4. **Exportez.** Appuyez sur `Export…` et donnez au fichier un nom terminé par
   `.xlsx` ou `.csv`.

## Bon à savoir

Chaque condition s'applique à toute la requête construite au-dessus d'elle, et
pas seulement à sa voisine : trois lignes donnent `((A) AND (B)) NOT (C)`, donc
un `NOT` exclut le terme de l'ensemble du résultat, et pas uniquement du dernier
mot-clé.

PubMed lui-même ne renvoie au maximum que **9 999** articles par recherche, quoi
que vous demandiez. C'est le vrai plafond de toute recherche, et la barre d'état
vous prévient quand une recherche l'a atteint.

## Retours et contributions

Tous les retours sont les bienvenus, et il n'est pas nécessaire d'être
développeur pour en faire. Si quelque chose n'est pas clair, manque, ou ne se
comporte pas comme vous l'attendiez, dites-le - c'est précisément ce qui oriente
la version suivante. Idem pour les idées : un champ que vous aimeriez voir
exporté, une étape que vous aimeriez plus rapide.

Le plus simple est d'ouvrir une
[issue](https://github.com/Arnoloh/PubMedSearch/issues) sur GitHub, en décrivant
ce que vous avez fait et ce que vous attendiez. Les contributions au code sont
tout aussi bienvenues.
