# Comment écrire un article de blog ?

## Introduction

La création d'un Article peut être realisée de deux manières:

 1. En créant un fichier Markdown sur le github Cdiscount IT-Blog
 2. Directement en Markdown sur le Wordpress.

Le format Markdown choisi correspond à celui de [GitHub](https://guides.github.com/pdfs/markdown-cheatsheet-online.pdf) et plus précisemment au format étendu [**Parsedown Extra**](https://michelf.ca/projects/php-markdown/extra/)

## 1. Création via markdown sur GitHub

L'interface WordPress étant lourde, la solution de rédiger des fichier MarkDown sur GitHub semble la plus simple.

Le principe est de créer pour chaque article un fichier Markdown qui sera ensuite synchronisé avec WordPress. Toute modification du fichier Markdown pourra être soit automatiquement répercuté sur le Wordpress, soit à la demande.

```csharp
/// <summary>
        /// Retrieves the boolean value contained in the key.
        /// </summary>
        /// <param name="key">The appSettings key.</param>
        /// <param name="siteId">The site identifier.</param>
        /// <param name="defaultReturnValue">Nullable default value returned if :
        /// - the key does not exist
        /// - the cast does not work.</param>
        /// <returns>The nullable boolean value contained in the key;
        /// default value returned if :
        /// - the key does not exist
        /// - the cast does not work.</returns>
        public static bool? GetAppSettingsToBool(string key, string siteId, bool? defaultReturnValue)
        {
            if (!string.IsNullOrEmpty(key))
            {
                string value = _internalConfigurationManager.AppSettings[key, siteId];
                if (!string.IsNullOrEmpty(value))
                {
                    bool returnValue;
                    if (bool.TryParse(value, out returnValue))
                    {
                        return returnValue;
                    }
                }
            }

            return defaultReturnValue;
        }

        /// <summary>
        /// Retrieves the integer value contained in the key.
        /// </summary>
        /// <param name="key">The appSettings key.</param>
        /// <param name="defaultReturnValue">Nullable default value returned if :
        /// - the key does not exist
        /// - the cast does not work.</param>
        /// <returns>The nullable integer value contained in the key;
        /// default value returned if :
        /// - the key does not exist
        /// - the cast does not work.</returns>
        public static int? GetAppSettingsToInt(string key, int? defaultReturnValue)
        {
            if (!string.IsNullOrEmpty(key))
            {
                string value = _internalConfigurationManager.AppSettings[key];
                if (!string.IsNullOrEmpty(value))
                {
                    int returnValue;
                    if (int.TryParse(value, out returnValue))
                    {
                        return returnValue;
                    }
                }
            }

            return defaultReturnValue;
        }
```

### 1.1 Récupérer le repo Git en local

La première étape est de cloner le repos Git sur votre poste via Git Bash pour les poste Linux ou via la commande Git pour les linuxiens.

```bash
git clone https://github.com/Cdiscount/IT-Blog.git
```

ou

```bash
git clone git@github.com:Cdiscount/IT-Blog.git
```

### 1.2 Créer un fichier Markdown

La première étape est de créer un fichier Markdown dans le repo git. Le fichier devra être nommé comme L'url de l'article pour faciliter la recherche du fichier Markdown par la suite.

Si l'url de votre article est *https://dev.cdiscount.com/blog/vive_docker/* le fichier devra se nommer *"vive_docker.md"*.

Afin de catégoriser les article, il est souhaitable de ranger un article dans un répertoire correspondant à sa catégorie.

Par example l'article suivant est dans la *"DevOps/Containerization"* viouios devrez créer un répertoire *"Docker"* contenant un répertoire *"Containerization"*

Une fois votre article écrit il vous faudra faire un commit local de vos modifications

```bash
git add .
git commit -m "<Your commit message>"
```

Une fois le Commit fait, il ne faudra pas oublier de pousser vos modifications sur le repos distant :

```bash
git push
```

### 1.3 Référencer le fichier MarkDown dans Wordpress

``` Bash
####### TODO --> Captures écrans WordPress
```

* Se Connecter sur le site le blog avec votre identifiant de domaine,

![Connection](https://github.com/Cdiscount/IT-Blog/raw/master/images/readme/connect.png)

* Ajouter un article via le menu d'administration en haut de Page,

![Ajouter un article](https://github.com/Cdiscount/IT-Blog/raw/master/images/readme/addnew.png)

* Ajouter un titre à votre article et pensez à modifier le permalink pour faciliter le référencement.

![Ajouter un titre](https://github.com/Cdiscount/IT-Blog/raw/master/images/readme/title.png)

* Selectionner la/les catégorie(s) de l'article,
   * 1 catégorie est obligatoire pour avoir une image sur l'article.

![Choix des catégories](https://github.com/Cdiscount/IT-Blog/raw/master/images/readme/cat.png)

* Ajouter une image personalisée à l'article,
  * Par défaut l'image de la catégorie sera utilisée.

![Image du post](https://github.com/Cdiscount/IT-Blog/raw/master/images/readme/selectimage.png)

* En bas de formulaire dans la zone "Markdown File Path" saisir le lien vers le fichier Markdown de l'article,
  * A chaque commit, sous GitHub l'article sera modifié sur le Blog (via une gestion d'ETAg).

![Lien l'article à github](https://github.com/Cdiscount/IT-Blog/raw/master/images/readme/markdown_file_path.png)

* Publier votre Article en mode Draft,
* Faite relire votre article par un autre redacteur du blog,

NB: Afin d'alimenter le blog régulièrement il est préférable d'échelonner la publication des articles. Si vous avez 2 articles à publier, veuillez espacer la publication d'au moins 1 jour.

## 2. Création via WordPress

Bon vous écrivez pour un __blog IT__, ce qui veux dire que vous êtes un __IT__!

Donc, **_vous devez retourner au chapitre 1_** !
