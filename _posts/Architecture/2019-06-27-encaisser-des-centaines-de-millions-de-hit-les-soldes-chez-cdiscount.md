---
layout: post
title:  "Encaisser des centaines de millions de Hit : les soldes chez Cdiscount"
author: fabien.poletti
categories: [ fr, events ]
image: "assets/images/Architecture/preparation_soldes/record_visites.PNG"
---

## Les soldes, un des moments forts de la vie du e-commerce
Cdiscount vit au rythme des grands évènements commerciaux de l’année : soldes d’hiver, french days, soldes d’été, black friday, et Noël. À chaque évènement l’enjeux pour Cdiscount se compte en centaines de millions d’euro de flux. 

Ces périodes sont essentielles pour notre activité : 
- Pour nos marchands internes et nos partenaires de la marketplace, qui proposent des offres attractives sur le site, afin de maximiser leur chiffre d’affaire 
- Pour nos clients grand public à la recherche des bonnes affaires 

Les soldes ont la particularité de répondre à un calendrier imposé par l’Etat, valable pour tous les marchands en ligne sur une même période. Afin d’imposer une concurrence équitable entre les magasins physique et les marchands en ligne, pas question d'afficher des promotions avant l’heure, c’est la Loi !  

Pour les clients grands public, les produits proposés à la vente voient ainsi leur prix baisser le jour J à 08h00 du matin. Le site doit donc être mis à jour à cet horaire exact afin que les marchands et les clients puissent faire des affaires autour des meilleures offres. 

Dans le cas contraire les impacts sont forts : les clients sont déçus et repartent du site, les marchands partenaires contactent le support Cdiscount, ce qui nous oblige à traiter un grand volume de réclamation en quelques minutes. Nous devons être irréprochables sur notre qualité de service afin que les affaires se déroulent sans accroc, et que les bonnes affaires puissent se conclure dans les meilleures conditions. La plateforme Cdisount est reconnue pour sa qualité, ces soldes d’été sont l’occasion de le prouver à nouveau ! 

## De J-60 à J-7 : le temps des optimisations techniques
Deux mois avant le début d’un évènement, les équipes se rassemblent en comité de pilotage hebdomadaire pour planifier la préparation. Sujet critique, le CTO est en charge de coordonner lui-même les tâches. 

D’expérience nous savons que la première action est de lister toutes les tâches qui devront être effectuée avant le lancement des soldes : nous devons purger la dette technique accumulée depuis le dernier évènement. Certains développements ont été effectués en quick win, il est temps de nettoyer ce qui doit l’être ! Les tickets sont ainsi envoyés dans les différentes roadmaps agiles et les projets pour être traités au fil de l’eau, dans les capacités dédiées aux actions techniques (entre 15% et 30% en fonction des équipes). Le suivi se fait naturellement sur un board kanban, au fur et à mesure des release.    

Pour ces soldes nous avons arbitré de lancer quelques actions techniques spécifiques d’optimisation de notre SI :

#### Encaisser les HIT sans scaler l’infra 
Mise en place des ETag sur les documents et les images, afin d’améliorer le temps de réponse et d’affichage des internautes qui naviguent sur notre site, et de moins solliciter notre infrastructure, tout en garantissant des informations à jour dans le navigateur client. La page est livrée avec des instructions d’expiration de cache, et un hash de la ressource. Ces hash sont renvoyés à chaque demande de ressource expirée par le navigateur, et notre back se charge de vérifier si une évolution a eu lieu depuis la dernière livraison au client. Si aucune modification n’a été apportée, un HTTP 304 (au lieu d’un 200) est renvoyé au browser du client en quelques dizaines de milli secondes, évitant un nouveau téléchargement complet qui aurait été plus long.
 
![]({{ site.baseurl }}/assets/images/Architecture/preparation_soldes/304.PNG "Le serveur ne renvoit pas la ressource mais un code 304")

Google propose une [explication complète](https://developers.google.com/web/fundamentals/performance/optimizing-content-efficiency/http-caching?hl=fr) et détaillée des avantages 

#### Optimiser le poids des images 
Les .PNG voient leur espace colorimétrique adapté en fonction de leur taille, pour un gain d’environ 10% en poids, et autant en temps de décodage. Encore quelques centaines de ko de gagné sur le poids du front, et en ms de temps de décodage processeur, ce qui raccourci le time to interactive. Un article détaillé permet de mieux appréhender le concept sous-jacent, mais l’idée est bien de comprendre que la différence est imperceptible pour nos utilisateurs. :)

A gauche l’image “non optimisée” sur un espace colorimétrique étendu, à droite la nouvelle. Re générer à la volée ces images permet aussi d’y aposer un ETag, pour faire coup double 

![]({{ site.baseurl }}/assets/images/Architecture/preparation_soldes/optim_images.PNG "L'optimisation permet de baisser le poids des images sans dégrader la qualité")

#### Intégrer plus d’offres, plus vite 
Intégration des mises à jour des offres de nos marchands sur le cluster RabbitMQ. Le vieux pooling SQL a vécu et a rendu de fiers services pour nous permettre de gérer 200 millions de mise à jour produits par jour. Pour atteindre la vitesse supérieure nous passons sur un vrai système pub/sub ! 

#### Accueillir les clients en douceur 
Afin de maitriser l’arrivée massive des internautes sur notre site à l’heure H exacte du lancement des soldes, une gestion fine de l’ouverture progressive de nos services a été mise en place, permettant de lisser la charge de connexion sur une période courte de quelques minutes. En multi device nous sommes capables de piloter finement le ramp up d’accès des utilisateurs pour accéder aux offres, en proposant des pages parking hébergées sur Azure, le cloud de Microsoft.  

#### Prêts pour les tests de vérification de la tenue à la charge ! 
Un des éléments fort de la préparation vient de la planification des tests de charge : Le point central du pilotage du lancement des soldes. Cdiscount possède une infrastructure hors norme de plusieurs milliers de serveurs : pas question pour des raisons budgétaires et environnementales d’avoir une préproduction iso à la production. Nos tests ont donc lieu directement sur la production. Le seul créneau disponible est donc la nuit 

Pendant les tests de charge plusieurs axes sont alors supervisés 

- Via Dynatrace pour la tenue à la charge notre back office legacy en .Net, de nos micro services en .Net core 
- Via zabbix pour les observables liée à la partie infra : CPU/RAM etc 
- via Elasticsearch outil  pour le suivi de logs 

Dès la fin des tests, les goulets d’étranglement sont identifiés et transformés en ticket, dont une certaine partie passe alors dans les pipes expedites des équipes concernées. 

Ces tests sont si importants que l’on souhaite passer au niveau supérieur de précision : un nouvel outil interne custom est en cours de développement. Sur ce blog vous trouverez prochainement un article dédié à Blaze Up :) 

## À J-7 à J : les  mises à jour des offres déferlent sur notre infrastructure
 A partir de J-7 ce sont plusieurs centaines de millions de mise à jour par jour sur les catalogues qui sont opérées, par nos marchands ou nos partenaires de la market place. Les produits voient leur prix évoluer, leur descriptif complété, en fonction de la démarque, du succès d’un produit etc. 

Cdiscount se doit de proposer le temps de mise à jour le plus réduit possible afin qu’un marchand puisse réagir à la loi de l’offre et de la demande. L’objectif est que même pendant le pic d’intégration de plusieurs dizaines de millions d’offre, le temps de traitement et de mise à disposition sur le front soit inférieur à l’heure. 

Pour se faire nous mettons à disposition plusieurs points d’entrée des mises à jour d’offre pour accueillir un maximum de marchands. La maintenance de ces deux entrées de données est essentielle, afin de garantir un attrait maximum pour notre market place. 

- Une incorporation de fichiers excel pour nos partenaires ayant des systèmes d’information manuels. Nous manipulons donc des librairies d’ouverture de fichier excel, de parsing etc. Un vrai bonheur :) 
- Un set d’api afin d’automatiser les traitements, en REST 

En parallèle un mode de prévisualision spécial soldes est proposée aux équipes métier. Nous anticipons donc ce que voient les internautes afin de préparer dans le moindre détail l’éditorialisation du site. 

## H-8 à H : la préparation pour le pic 

Cdiscount tient via son ADN commerçante à maintenir un cérémonial d’ouverture pour les offres. Le site ferme théâtralement pour la seule fois de l’année vers 04h00, pour rouvrir à 08h00 avec les meilleures offres du web. Nous faisons alors face, dès la première minute d’ouverture, à un pic de connexion que peu de sites rencontrent : en quelques secondes notre infrastructure fait face à des millions de HIT par seconde.  

Toute la stack est alors sollicitée, et la bonne utilisation du cache est essentielle. 

Le Content Delivery Network (CDN) se retrouve en charge de livrer les assets cachés le plus rapidement possible : images, css, js, une partie du html. Historiquement nous avons utilisé les acteurs du marché afin d’optimiser la vitesse de livraison de nos pages. Fin 2016 lors de la migration HTTPS et HTTP2, nous avons décidé d’aller plus loin et de reprendre en main la technologie en créant notre solution maison, sur deux pops parisiens. Basé sur des outils open source type Varnish, il embarque un mini cluster base sur un orchestrateur de conteneur. Le CDN est prévu pour expulser plus de 17 Gb/s en pic ou 150000 req/s pour la partie image en cache par cluster.

 
![]({{ site.baseurl }}/assets/images/Architecture/preparation_soldes/archi_cdn.PNG "L'architecture des briques open source de notre CDN")

Et le CDN est en coupure de tous les HIT arrivant sur l'infrastructure

![]({{ site.baseurl }}/assets/images/Architecture/preparation_soldes/flux_cdn.PNG "Les flux vers l'infra")

## Résultat : encore un record  battu !

Encore un pic de charge tenue avec une QoS proche de 100% ! Quelques ajustements en temps réel ont été nécessaire, rendus possibles par un suivi temps réel de nos logs, de nos métriques et des infos remontées par la stack. 

Le pic a été bien dessiné dès l’ouverture, battant un nouveau record ! 

![]({{ site.baseurl }}/assets/images/Architecture/preparation_soldes/record_visites.PNG "Record battu !")

Le site va pour les prochaines semaines rester en mode soldes, et nous reviendrons en mode "normal” le 06 août. En attendant de prochaines améliorations, nous livrons tous les jours. Venez nous rejoindre pour l'aventure !