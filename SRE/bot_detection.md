# Pourquoi avons-nous conçu un détecteur de bot pour notre site de e-commerce

![](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/SRE/botdetection/Botdetection.png)



## Contexte

Comme beaucoup de sites internet, de nombreux bots [^1] parcourent le site de Cdiscount.
Il y en a de plusieurs types :

- les bots des moteurs de recherche : ils indexent le web.

- les bots des sites comparateurs de prix.

- les bots des autres sites de e-commerce :
ils leur permettent de s’aligner sur le prix d’une promotion ou de détecter les produits qui se vendent, mais non disponibles sur leur site.

- les bots des vendeurs qui veulent vérifier que leurs offres sont bien présentes.

- les bots malveillants qui veulent trouver des failles ou faire tomber le site.

La plupart des bots ne sont pas nocifs pour Cdiscount, certains sont même voulus et recherchés, comme ceux des moteurs de recherche (Google, Bing...), qui permettent à Cdiscount d'apparaître en tête des résultats de recherche.
Mais en cumulé, il y a parfois plus de trafic sur le site généré par des bots que par des visiteurs ce qui représente un coût pour l’infrastructure.
Des bots vraiment agressifs pourraient notamment rendre le site indisponible lors d'événements importants comme le Black Friday en générant plus de trafic qu'à l'habitude.
C’est pour cela qu’il nous fallait créer un système permettant d'identifier le trafic provenant de bots pour traiter différemment les requêtes effectuées par les humains de celles effectuées par des bots potentiellement malveillants.

## Les enjeux

- Analyse temps réel.

- Ne pas avoir d'incidence sur le temps de réponse des sites.

- Applicable au site PC aussi bien qu’au site mobile.

- Mesurer précisément la charge induite par la détection.

- Savoir qui crawle (récupérer de l'information) le site et reconnaitre des patterns typiques.

- Avoir une solution souple et adaptable sur le long terme face aux évolutions des patterns.

- Prioriser le trafic pour les utilisateurs.

# Comment avons-nous conçu un détecteur de bot pour notre site de e-commerce

Pour détecter un bot, l’unique source d’information est la requête HTTP.
Il faut donc pouvoir analyser et essayer de classifier cette requête.

![](https://raw.githubusercontent.com/Cdiscount/IT-Blog/master/images/SRE/botdetection/flux.png)

_Le schéma d'infrastructure_

Pour récupérer les informations contenues dans la requête HTTP, nous avons utilisé [OpenResty](https://openresty.org/), une distribution de Nginx avec support de Lua [^2]) en mode "reverse proxy"[^3].
Le support de Lua nous permet d'étendre facilement les fonctionnalités du serveur web.
Nous avons ainsi pu personnaliser les données à récupérer de l'access log (le format de base ne convenait pas : certaines informations n'étaient pas nécessaires comme les cookies de l'AB testing alors d'autres étaient manquante comme la géolocalisation).
Le support de Lua permet de filtrer beaucoup plus finement les données envoyées à analyser et on peut également changer la configuration de filtrage des serveurs OpenResty à chaud.
Tout le trafic passe par les serveurs OpenResty.

Les serveurs OpenResty effectuent deux tâches :

- Ils vérifient si on est en présence d’un bot via une base de données clé-valeur.

- Ils transmettent les informations utiles de la requête à un service de traitement de flux d’événements temps réel (Kafka) via des collecteurs Fluentd.

Fluentd a été choisi pour ses très bonnes performances, sa capacité à chiffrer la donnée et son connecteur Kafka.

Le service de traitement de flux d’événements est composé de plusieurs [Kafka Streams](https://kafka.apache.org/documentation/streams/)(Les Kafka Streams sont des micros services qui traitent le flux de données en continu, ils sont distribués et extensibles) déployés dans un Kubernetes :

- un premier service “Enrich Kafka Stream” permet d’enrichir le log et de le simplifier (le type de page et de ressource, la localisation de l’IP, le type de device [de terminal], si c’est un client connu et s’il a déjà commandé)

- le second service “Stats Aggregator Kafka Stream” permet de créer des statistiques sur les visites.
Sur une fenêtre de temps, on vient compter pour chaque Fingerprint [^4] le nombre de requêtes effectuées.
On a donc par exemple x requêtes sur la page d’accueil, x sur des fiches produits, x sur des images...

- le troisième permet “Bot Tagging Kafka Stream”, à partir de règles statiques et d’un modèle d’apprentissage automatique [H2O](https://www.h2o.ai/), de prédire si un utilisateur est légitime ou si c’est un bot.
Dans le cas d’un bot, on va écrire son Fingerprint et sa catégorie (Couleur) dans une base de données MongoDB.
Il sera écrit avec un TTL pour ne pas bloquer trop longtemps un faux positif.

En plus de ces 3 services, un service “Datalake Kafka Sream” envoie les données sur un Datalake Azure.
Les données qui y sont stockées sont utilisées pour détecter a posteriori des bots et pour réentraîner le modèle.

En parallèle, un service “Monitoring Kafka Stream” permet de faire du monitoring sur le flux et de consulter l'état du trafic (volume, nombre de bots détectés...) via des dashboards Grafana.

Nous avons choisi Kafka et Kafka Streams, pour leur aspect temps réel et leur rapidité.
Nous avons choisi MongoDB pour son mode clé document et sa gestion des TTL (durée de vie).

Le [Model H2O](https://www.h2o.ai/)[^5] est généré à partir d’un jeu de données extraites du Datalake.
Il est ensuite nécessaire qu’un humain détecte manuellement les bots pour que le modèle soit efficace.
Une fois généré, le modèle nous donne un score sur la pertinence de la détection.
Nous avons choisi de l’associer à des couleurs.
Par exemple de 50 % à 90 % le bot présumé sera gris et au-dessus de 90 % il sera noir.
D'autres "Couleurs" pourraient être ajoutées si on détecte le type de bot.

Une fois les bots détectés et enregistrés dans la base de données MongoDB, une tâche permet aux OpenResty de mettre à jour leurs bases de données internes avec les couples “Fingerprint et Couleur”.
Un entête HTTP est ainsi ajouté aux requêtes de bots pour indiquer leur catégorie.

Grâce à cet entête, les équilibreurs de charges (load balancer) peuvent, soit rediriger la requête du bot sur des serveurs dédiés aux bots (avec de nombreux caches par exemple) soit les bloquer en cas de trop forte affluence.

# Résultat

La partie qui permet de taguer les bots prend dans 50 % des cas moins de 0,2 ms, dans 90 % des cas moins de 0,5 ms, dans 99 % des cas moins de 1ms et dans 99,99 % des cas moins de 2 ms.

On arrive à traiter jusqu’à 6000 messages par seconde avec 6 nœuds Kubernetes et 3 nœuds Kafka de 8 cœurs et 64 Go de RAM.

Même si on sait que l'on ne détecte pas la totalité des bots, on arrive quand même à un pourcentage de 40 à 80 % de bot pour chaque page requête (en excluant les requêtes statiques [JS, CSS, images…])

[^1]: Un bot (mot anglais, contraction de "robot") est un agent logiciel interagissant avec les serveurs (site web, application mobile, API...) de façon automatique ou semi-automatique.

[^2]: Lua est un langage de script libre, réflexif et impératif.
Créé en 1993, il est conçu de manière à pouvoir être embarqué au sein d'autres applications afin d'étendre celles-ci.

[^3]: Le reverse proxy permet à un utilisateur d'internet d'accéder à des serveurs internes.

[^4]: Un Fingerprint est une donnée qui permet d’identifier un utilisateur ou un bot de manière la plus unique possible.
Ça peut être seulement son IP ou bien un couple de plusieurs valeurs comme IP et cookie, IP user agent.

[^5]: H2O est un outil d’apprentissage automatique (Machine Learning) créant des modèles prédictifs.

*[TTL]: Time-To-Live

