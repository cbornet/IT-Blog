# Comment écrire un article de blog ?

## Introduction

La création d'un Article se réalise en créant un fichier Markdown sur le GitHub Cdiscount IT-Blog

Le format Markdown choisi correspond à celui de [GitHub](https://guides.github.com/pdfs/markdown-cheatsheet-online.pdf) et plus précisemment au format étendu [**Parsedown Extra**](https://michelf.ca/projects/php-markdown/extra/)

## 1. Création via markdown sur GitHub

### 1.1 Récupérer le repo Git en local

La première étape est de cloner le repos Git sur votre poste via Git Bash pour les postes Linux ou via la commande Git pour les linuxiens.

```bash
git clone https://github.com/Cdiscount/IT-Blog.git
```

ou

```bash
git clone git@github.com:Cdiscount/IT-Blog.git
```

### 1.2 Créer un fichier Markdown

La première étape est de créer un fichier Markdown dans le repo git. Le fichier devra être nommé comme l'url de l'article pour faciliter la recherche du fichier Markdown par la suite.

Si l'url de votre article est *https://dev.cdiscount.com/blog/vive_docker/* le fichier devra se nommer *"vive_docker.md"*.

Afin de catégoriser les articles, il est souhaitable de ranger un article dans un répertoire correspondant à sa catégorie.

Par exemple l'article suivant est dans la *"DevOps/Containerization"* vous devrez créer un répertoire *"Docker"* contenant un répertoire *"Containerization"*

Une fois votre article écrit il vous faudra faire un commit local de vos modifications

```bash
git add .
git commit -m "<Your commit message>"
```

Une fois le commit fait, il ne faudra pas oublier de pousser vos modifications sur le repos distant :

```bash
git push
```

NB: Afin d'alimenter le blog régulièrement il est préférable d'échelonner la publication des articles. Si vous avez 2 articles à publier, veuillez espacer la publication d'au moins 1 jour.
