# Comment écrire un article de blog ?

## Introduction

La création d'un Article se réalise en créant un fichier Markdown sur le GitHub Cdiscount IT-Blog

Le format Markdown choisi correspond à celui de [GitHub](https://guides.github.com/pdfs/markdown-cheatsheet-online.pdf) et plus précisemment au format étendu [**Parsedown Extra**](https://michelf.ca/projects/php-markdown/extra/)

## 1. Création d'un article sur GitHub

### 1.1 Récupérer le repo Git en local

La première étape est de cloner le repos Git sur votre poste
```bash
git clone https://github.com/Cdiscount/IT-Blog.git
```
ou
```bash
git clone git@github.com:Cdiscount/IT-Blog.git
```

### 1.2 Créer un article draft

La première étape est de créer un fichier Markdown dans le repo git dans le repertoire `_drafts`.
Le fichier devra être nommé comme l'url de l'article pour faciliter la recherche du fichier Markdown par la suite.

Si l'url de votre article est *https://techblog.cdiscount.com/vive_docker/* le fichier devra se nommer *"vive_docker.md"*.

Afin de catégoriser les articles, il est souhaitable de ranger un article dans un répertoire correspondant à sa catégorie.

Par exemple l'article suivant est dans la *"DevOps/Containerization"* vous devrez créer un répertoire *"Docker"* contenant un répertoire *"Containerization"*

Une fois votre article écrit il vous faudra faire un commit local de vos modifications dans une branche
```bash
git checkout -b ma-branche
git add .
git commit -m "<Your commit message>"
```
Une fois le commit fait, il ne faudra pas oublier de pousser vos modifications sur le repos distant :
```bash
git push origin ma-branche
```
Puis ouvrir une Pull Request sur GitHub afin que le changement soit revu et commenté avant d'être fusionné sur `master`.

### 1.3 Publier l'article

Pour publier l'article, il suffit de le déplacer du répertoire `_drafts` vers le répertoire `_posts` et de le renommer en le préfixant par la date de publication au format `YYYY-MM-DD-titre-de-l-article.md`.

De la même façon que pour le draft, faire un commit local dans une branche, pousser la branche et ouvrir une Pull Request.

Lorsque la PR est fusionnée, Github se charge de générer le blog Jekyll et de le déployer automatiquement.

NB: Afin d'alimenter le blog régulièrement il est préférable d'échelonner la publication des articles. Si vous avez 2 articles à publier, veuillez espacer la publication d'au moins 1 jour.

## Astuces lors de la rédaction de l'article

### Lancer le blog en local

Pour utiliser une version locale du blog pour valider vos modifications, il y a deux possibilités:
* Installer et lancer [Jekyll](https://jekyllrb.com/docs/)
* Utiliser `docker-compose` (plus simple, pas besoin d'installer ruby)

Pour lancer le blog avec `docker-compose`
```bash
docker-compose up
```
Le blog est visible sur http://localhost:4000 . Les articles drafts sont exposés.

### Live-reload

Utiliser `brower-sync` pour recharger automatiquement le blog local dès qu'une modification est faite.

Lancer le blog en local (cf ci-dessus)

Installer brower-sync

```bash
sudo npm install -g browser-sync
```

Lancer browser-sync
```
browser-sync start --proxy "localhost:4000" --files "_site/*.*" --reloadDelay "2000"
```
Le blog avec live-reload est visible sur http://localhost:3000

## Crédits

Le blog a été généré en utilisant:
* [Jekyll](https://jekyllrb.com/)
* Le thème Jekyll [Mediumish](https://github.com/wowthemesnet/mediumish-theme-jekyll) de wowthemes.net