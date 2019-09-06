---
layout: post
title: "Remplacer un tracking côté client par un tracking côté serveur avec Puppeteer"
author: gregory.guichard
categories: [fr, cloud, web]
image: assets/images/Architecture/tracking_server/thumbnail.jpg
---

Le tracking fait maintenant partie intégrante du web.
Tous les sites web disposent de scripts qui permettent de suivre les actions de ses utilisateurs afin d'améliorer leur expérience, de comprendre leur comportement et de leur proposer des offres qui correspondent à leurs besoins.
Cependant ces trackers demandent des ressources aux terminaux des clients pour leurs exécutions, et cela peut donc ralentir la navigation et nuire à l'expérience utilisateur.

## Comment fonctionne un tracker

Il existe de nombreux trackers, les plus connus sont le [pixel Facebook](https://fr-fr.facebook.com/business/) ou encore [Google Analytics](https://analytics.google.com/analytics/web/).
Ils permettent de suivre le nombre de visites, les pages les plus consultées, les actions des utilisateurs ou encore les caractéristiques des utilisateurs (résolution, terminal et navigateur utilisé, système d'exploitation, etc.).
Un tracker est un élément ajouté à une page HTML (eg. un script Javascript ou une image) et qui va être exécuté sur le navigateur du client pour transmettre des informations à un serveur distant où elles seront collectées et analysées.
Les trackers ont des finalités différentes, certains trackers permettent d'améliorer la pertinence du contenu, de s'adapter aux usages des utlisateurs, d'améliorer le référencement, etc. C'est pourquoi il est fréquent d'avoir plusieurs trackers sur un même site.
Le tracking s'accompagne souvent d'un cookie qui est installé sur le terminal client, afin de le suivre pendant sa navigation sur le site et éventuellement lors de ses prochaines visites.

![tracking client vs tracking serveur]({{ site.baseurl }}/assets/images/Architecture/tracking_server/tracking-client-serveur.png)

## Quels sont les avantages d'un tracking Back-End ?

En plus de son propre tracking, il est usuel d'installer les trackers de partenaires qui vont collecter les données sur leurs propres serveurs pour les analyser et présenter des résultats consolidés.
Dans le cas de sites évolués tels que Cdiscount, le nombre de partenaires de tracking peut devenir important.
Il devient alors intéressant de remplacer tous ces trackers par un tracker unique et de faire les appels vers les partenaires côté serveur.
Les avantages sont :

- **Qualité des données** : Les trackers s'exécutent sur le périphérique de l'utilisateur.
  Or il se peut que certains trackers ne s'exécutent pas ou s'exécutent mal et ceci crée une hétérogénéité dans les données remontées.
  En exécutant ces trackers sur les serveurs au lieu du navigateur, on peut contrôler qu'ils s'exécutent correctement et disposer ainsi de données de qualité et homogènes.
  Il est même possible de rejouer les trackers a posteriori en cas de besoin (eg. site d'un partenaire injoignable)
- **Meilleure expérience client** : Les trackers utilisent les ressources matérielles des utilisateurs, et pour les périphériques les plus modestes cela peut représenter une charge importante.
  Libérer les utilisateurs de l'exécution de ces trackers permet une meilleure fluidité lors de leur navigation sur le site.
  Cela permet également de diminuer le nombre de cookies installés sur le navigateur.

## Les problématiques liées au tracking Back-End

Deux cas se présentent :

- L'API de tracking du partenaire est publique et documentée : dans ce cas-là il n'y a pas de difficulté particulière. Il suffit d'exécuter une requête HTTP avec les données des clients.
- L'API de tracking du partenaire n'est pas connue : dans ce cas-là il faut exécuter le tracker sur nos serveurs afin d'imiter le comportement des utilisateurs. Ce cas est plus compliqué, et c'est celui-ci qui va nous intéresser ici.

![Schéma tracker]({{ site.baseurl }}/assets/images/Architecture/tracking_server/server_side_tracking.png)

Pour assurer un tracking côté serveur lorsque l'API de tracking du partenaire n'est pas connue, il faut :

- Collecter les données nécessaires au tracking des partenaires dans un tracker Cdiscount unique.
- Exécuter le code JavaScript des trackers dans un environnement simulant le navigateur de l'utilisateur et son contexte.
  Ceci en étant agnostique de l'implémentation, c'est-à-dire sans connaître le code et donc le comportement et les informations attendues par le tracker.

Simuler la navigation sur plusieurs centaines de pages vues par seconde peut s'avérer gourmand en ressources, la solution retenue doit être optimisée pour éviter des coûts de traitement trop importants.

## Comment simuler un navigateur côté Back-End

Pour simuler un navigateur côté Back-End nous avons utilisé [**Puppeteer**](https://developers.google.com/web/tools/puppeteer).
Puppeteer est un framework NodeJS qui propose une API haut niveau pour contrôler [**Chromium**](https://www.chromium.org/Home) par le biais du [**Chrome DevTool Protocol**](https://chromedevtools.github.io/devtools-protocol/).
Puppeteer est un projet Google utilisé à l'origine pour tester les interfaces de ses applications Web.
Cette librairie est très complète, stable, performante et bien maintenue.
Puppeteer va permettre d'exécuter les scripts de tracking dans un navigateur Web pour lequel on aura émulé le contexte des utilisateurs.
Le cycle de vie de notre application Puppeteer est le suivant :

1. Création d'un navigateur (Chromium par défaut) via Puppeteer
2. Récupération des données de tracking collectées (URL, objets JavaScript _navigator_, _window_, _document_, etc.).
3. Récupération également des cookies précédemment enregistrés si ce n'est pas la première exécution du tracker pour cet utilisateur.
4. Configuration du contexte du navigateur via l'API de Pupeteer.
5. Exécution des trackers. À la fin de l'exécution, le tracker envoie les informations collectées au serveur du partenaire par des requêtes HTTP. Le tracker va également générer un cookie au besoin. Ce cookie est sauvegardé pour être réutilisé si l'utilisateur visite une autre page.
6. Fermeture du navigateur et retour à l'étape 1.

Ceci permet de simuler correctement la navigation des utilisateurs, mais ce n'est pas optimisé.
Sur le site de Cdiscount, il y a plusieurs centaines de pages vues par secondes, et il y a plusieurs trackers par page.
Afin de pouvoir de tenir le trafic présent sur le site nous avons donc du optimiser notre stratégie de tracking Back-End :

- **Mutualisation des trackers** : le même contexte d'exécution est utilisé pour plusieurs trackers.
  La récupération et la mise en place du contexte (c'est à dire des variables utilisateur) sur le navigateur virtuel sont coûteuses, c'est pourquoi plusieurs trackers sont exécutés dans le même contexte.

- **Stratégie de rafraichissement** : la page est rafraichie au lieu de détruire et de reconstruire le navigateur.
  Cela permet également d'utiliser les mécanismes de cache du navigateur (pour les images, mais également pour la construction du DOM).

- **Enrichissiment des données au préalable** : les données de tracking sont reçues sur un topic Kafka.
  Des Kafka Streams sont utilisés pour enrichir les données de tracking avec le cookie de tracking correspondant s'il a déjà été généré.

- **Délégation de l'exécution des requêtes** : l'exécution des requêtes par le navigateur est coûteuse. Le navigateur doit attendre la réponse de la requête HTTP, gérer les échecs et les renvois avant de pouvoir passer au tracker suivant.
  Cela ralentit l'exécution des trackers. C'est pourquoi les requêtes à exécuter sont publiées dans un topic Kafka pour être exécutées de façon asynchrone par un micro-service dédié.

- **Stockage des cookies dans un cache** : si c'est la première fois qu'un tracker est exécuté, il génère en général un cookie qui doit être réutilisé lors de la prochaine exécution.
  Cela permet de distinguer les utilisateurs et de suivre leur navigation.
  Ce cookie de tracking est donc stocké dans un cache CouchBase (pour être récupéré au moment de l'enrichissement).

## Architecture Proof-of-Concept

![]({{ site.baseurl }}/assets/images/Architecture/tracking_server/architecture.png)

1. Lorqu'un utilisateur visite une page sur Cdiscount.com, un script de tracking unique récupère les informations nécessaires aux partenaires de tracking.
   Il va également poser un cookie qui permettra d'identifier l'utilisateur pendant sa navigation.
2. Les données collectées sont ensuite envoyées sur un serveur de Cdiscount.
3. Un micro-service développé en Java publie ces données dans un topic Kafka.
   Chaque message correspond à une exécution du script de tracking
4. Une application Kafka Streams enrichit les messages avec les cookies des trackers partenaires s'ils existent déjà pour cet utilisateur dans Couchbase (voir plus loin).
5. Un micro-service consomme les messages enrichis et les utilise pour configurer des navigateurs et leur faire exécuter les scripts de tracking des partenaires.
   Plutôt que d'exécuter les requêtes HTTP vers les sites des partenaires, ces requêtes sont capturées et publiées dans un topic Kafka.
   Si le tracker génère un cookie, celui-ci est stocké dans Couchbase afin de pouvoir être utilisé à l'étape 4.
6. Un micro-service Java récupère les requêtes HTTP à exécuter vers les partenaires dans le topic Kafka et les exécute de façon fiable.

## Conclusion

Nous avons vu comment déployer un tracking côté serveur.
Ce type de tracking apporte son lot de difficultés et de limitations :

- Les informations que l'on envoit aux partenaires doivent être connues à l'avance afin de les récupérer auprès du client et de pouvoir les simuler dans nos navigateurs virtuels.
- Certains trackers ont des comportements particuliers (e.g une temporisation de quelques secondes ou attente d'un événement avant d'envoyer une requête) et peuvent donc dégrader nos performances.
- La simulation de navigateurs nécessite du temps CPU et également de la maintenance. Cela induit un coût plus important que le tracking côté client.

Néanmoins le tracking Back-End permet de décharger l'utilisateur de l'exécution des scripts et donc de lui proposer une meilleure expérience de navigation.
Il permet également de contrôler la cohérence et la qualité des données fournies aux trackers partenaires et donc la cohérence des analyses fournies par ces partenaires.
