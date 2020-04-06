---
layout: post
title:  "Garantir la livraison des messages et la résilience sur plusieurs datacenters avec Apache Pulsar"
author: rd.team
categories: [ fr, cloud ]
image: assets/images/Architecture/resilient-messaging/mailboxes.jpg
precontent: "[🇬🇧 To English version](../ensure-cross-datacenter-guaranteed-message-delivery-and-resilience-with-apache-pulsar)<br>
_Grégory Guichard, R&D Engineer at Cdiscount_<br>
_Romain Castagnet, Site Reliability Engineer at Cdiscount_<br>
_Christophe Bornet, R&D Manager at Cdiscount_"
---
Chez Cdiscount, nous traitons d'importants volumes de données en temps réel grâce à des systèmes de messaging distribués. Pour nos besoins de diffusion d'événements, nous utilisons actuellement [Kafka](https://kafka.apache.org/ "Kafka") et pour nos besoins de queue, nous utilisons [RabbitMQ](https://www.rabbitmq.com/ "RabbitMQ"). En raison de la nature des données traitées par Cdiscount (commandes, paiements, etc...), il est impératif d'avoir une garantie très forte sur la livraison des messages (ne perdre aucun messages) avec la plus grande disponibilité possible, même en cas de perte subite d'un de nos datacenters. Nous avions des difficultés à garantir ce niveau d'exigence avec Kafka et RabbitMQ et cela nous a amené à évaluer [Apache Pulsar](https://pulsar.apache.org/), la toute dernière technologie apparue récemment et qui met en avant de fortes promesses dans ce domaine.

Pré-requis pour les tests: ce blog utilise [docker](https://docs.docker.com/install/) et [docker-compose](https://docs.docker.com/compose/install/) pour démarrer simplement les noeuds des clusters dans des conteneurs isolés.

## Qu'est ce que Pulsar ?

Apache Pulsar est une solution de messagerie distribuée open-source créée à l'origine par Yahoo et faisant désormais partie de l'Apache Software Foundation.

### Architecture

Dans l'architecture de Pulsar, nous retrouvons trois composants :

- **Broker** : composant stateless en charge de traiter les requêtes des clients, par le biais du protocole Pulsar ou d'un proxy websocket. Il dispose aussi d'une API REST pour les opérations d'administration.
- **[BookKeeper](https://bookkeeper.apache.org/)** : stockage distribué, scalable, performant et résistant aux pannes. Pulsar utilise BookKeeper pour le stockage persistent des données. Un cluster BookKeeper est composé de plusieurs noeuds appelés bookies.
- **[Zookeeper](https://zookeeper.apache.org/)** : service assurant la coordination des brokers et de BookKeeper et dans lequel sont stockés également les meta-données.

![](https://static1.squarespace.com/static/56894e581c1210fead06f878/t/5bb4bfb271c10b7ebdf3ca8e/1538572215597/PulsarBkZkCluster.png?format=750w)

- **Topic** : structure dans laquelle sont publiés et consommés les messages. Dans Pulsar ou  Kafka, les topics sont persistés donc les messages n'ont pas besoin d'être consommés dès qu'il sont publiés et plusieurs consommateurs peuvent lire les même messages à des index et des vitesses différents.
- **Namespace** : permet de configurer la politique des topics qu'il va contenir (rétention, ACL, persistence, etc.)
- **Tenant** : Pulsar est multi-tenant, chaque tenant ayant son propre schéma d'authentification et d'autorisation. Un tenant peut contenir plusieurs namespaces.

### Pourquoi nous sommes nous intéressé à Pulsar ?

Pulsar possède plusieurs caractéristiques qui le rendent unique par rapport aux autres systèmes de messaging:

- **Diffusion d'événement mais aussi Queue de messages** : en permettant à plusieurs groupes de consommateurs d'avoir leur propre index sur la file de message, Pulsar permet les usages de diffusion d'événement selon le même principe que Kafka. Mais Pulsar permet aussi de valider le traitement des messages individuellement sans bloquer la file de message (ou sa partition) ce qui n'est pas supporté par Kafka et qui est indispensable pour les usages de queue de messages tels que possibles avec RabbitMQ.
- **Réplication synchrone** : la réplication synchrone est assurée par BookKeeper et permet de garantir la durabilité des messages même en cas de perte de bookies. La fonctionalité `rack-awareness` permet de s'assurer que les messages ne sont acquittés qu'une fois qu'ils ont été écrits sur des noeuds appartenant à des datacenters distincts.
- **Réplication asynchrone native** : la réplication asynchrone est directement intégrée à la solution open-source et ne fait pas partie d'une offre payante. Elle permet de répliquer les messages entre clusters distincts. Il faut noter que les index de lecture des consommateurs sont locaux à un cluster et qu'il est compliqué de basculer un consommateur sur un cluster répliqué en le faisant reprendre au bon index.
- **Montée en charge simplifiée** : les brokers étant stateless, il est très simple d'ajouter des noeuds au cluster et même de faire de l'auto-scaling. Le système de ledgers et de distribution des partitions sur plusieurs noeuds permet d'ajouter dynamiquement des bookies au cluster BookKeeper sans avoir la tâche délicate de rééquilibrer les partitions.
- **Isolation des régions** : il est possible de configurer le cluster pour que les consommations de messages n'impliquent les noeuds que d'une seule région en mode nominal avec une bascule sur les noeuds d'une autre région en cas de problème. Plus de détails ci-dessous.

## Comment mettre en place un cluster actif/passif en réplication synchrone avec Pulsar ?

### Présentation

Nous allons mettre en place un cluster Pulsar étendu sur 2 régions/datacenters avec un datacenter actif et un passif qui n'est utilisé qu'en cas de défaillance du datacenter actif. En mode nominal, les clients consomment sur le même datacenter qu'eux, ce qui réduit la latence et la coûteuse bande passante inter-datacenter utilisée.

1. Pulsar est configuré pour que les brokers choisis pour les partitions d'un topic soient sur un unique datacenter.
2. Un client publie des données sur ce topic.
3. Les données sont persistées de façon synchrone sur au moins un bookie du datacenter actif et au moins un bookie du datacenter passif. Ainsi en cas de perte du datacenter actif, les données seront toujours disponibles sur le second datacenter sans possibilité de perdre des messages.
4. Lors de la consommation, le client se connecte au broker propriétaire du topic, ce broker va lire préférentiellement les données sur un bookie de la même région que lui.

En cas de panne du datacenter actif, les brokers du datacenter passif deviennent automatiquement utilisables pour publier/consommer des messages. Comme il n'y a qu'un seul cluster Pulsar, la bascule est transparente pour les clients.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/namespace_isolation.png)

Plusieurs configurations doivent être mises en place afin de mettre en place un Pulsar actif/passif synchrone :

- **_Namespace Isolation Policy_** : permet d'isoler un namespace sur un ensemble de brokers. Cela permet de s'assurer assure que les brokers propriétaires des partitions des topics sont choisis prioritairement sur une région. S'il n'y a plus assez de noeuds disponibles sur cette région (eg. en cas d'incident) alors les brokers de l'autre région peuvent être choisis.
- **_Rack Awareness_** : permet que les messages soient répliqués de façon synchrone sur des bookies appartenant à des racks différents.
- **_Region Awareness_** : permet que les messages soient répliqués de façon synchrone sur des bookies appartenant à des régions différentes.
- **_Read reordering_** : permet de privilégier la lecture des messages sur des bookies appartenant à la même région que le broker (lorque la fonctionnalité `Region Awareness` est utilisée)

> Note: l'exposition des fonctionnalités `Region Awareness` et `Read Reordering` au projet Apache Pulsar est une contribution de Cdiscount.

### Démonstration avec Docker

Nous allons construire une architecture comprenant 2 datacenters avec chacun 2 brokers et 2 bookies, ainsi qu'1 ZooKeeper commun.

Le premier datacenter représentera la région **_eu_** où l'on retrouvera 2 brokers et 2 bookies qui seront préfixés par **_eu_**. Nous retrouverons la même configuration sur le deuxième datacenter qui représente la région **_us_**.

Sur chaque région nous créerons un namespace en configuration active sur la région en question et passive sur l'autre.

Les commandes ci-dessous sont à éxécuter depuis la racine du dossier [docker](https://github.com/Cdiscount/IT-Blog/tree/master/samples/Architecture/resilient-messaging/docker).

#### Configuration

Nous commençons par créer le cluster ZooKeeper:

```
docker-compose -f docker-compose_zk.yml up -d
```

Nous créons ensuite le cluster **_mycluster_** dans ZooKeeper :

```
docker exec -it zk bin/pulsar initialize-cluster-metadata \
      --cluster mycluster \
      --zookeeper zk:2181 \
      --configuration-store zk:2181 \
      --web-service-url http://pulsar1-eu:8080 \
      --broker-service-url pulsar://pulsar1-eu:6650
```
Puis nous créons les brokers et les bookies. Les brokers sont configurés pour utiliser les fonctionnalités `Region-aware placement policy` et `Read reordering`.
```
docker-compose -f docker-compose_sync.yml up -d
```

Il faut ensuite définir les régions et les racks sur lesquels vont se placer les bookies et les brokers grâce à la commande **_set-bookie-rack_**.

```
docker exec -it pulsar1-eu bin/pulsar-admin bookies set-bookie-rack -b bk1-eu:3181 -r eu/1
docker exec -it pulsar1-eu bin/pulsar-admin bookies set-bookie-rack -b bk2-eu:3181 -r eu/1
docker exec -it pulsar1-eu bin/pulsar-admin bookies set-bookie-rack -b bk1-us:3181 -r us/1
docker exec -it pulsar1-eu bin/pulsar-admin bookies set-bookie-rack -b bk2-us:3181 -r us/1
docker exec -it pulsar1-eu bin/pulsar-admin bookies set-bookie-rack -b pulsar1-eu:6650 -r eu/1
docker exec -it pulsar1-eu bin/pulsar-admin bookies set-bookie-rack -b pulsar2-eu:6650 -r eu/1
docker exec -it pulsar1-eu bin/pulsar-admin bookies set-bookie-rack -b pulsar1-us:6650 -r us/1
docker exec -it pulsar1-eu bin/pulsar-admin bookies set-bookie-rack -b pulsar2-us:6650 -r us/1
```

Nous pouvons vérifier la région assignée à chaque bookie grâce à la commande :

```
docker exec -it pulsar1-eu bin/pulsar-admin bookies racks-placement
```

Nous créons ensuite un tenant **_mytenant_**, et deux namespaces **_mytenant/eu_** et **_mytenant/us_** qui seront spécifiques à chaque région.

```
docker exec -it pulsar1-eu bin/pulsar-admin tenants create mytenant \
  --admin-roles admin-role \
  --allowed-clusters mycluster
docker exec -it pulsar1-eu bin/pulsar-admin namespaces create mytenant/eu
docker exec -it pulsar1-eu bin/pulsar-admin namespaces create mytenant/us
```

Nous définissons ensuite une _politique d'isolation de namespace_ pour chaque région. Pour le namespace **_mytenant/eu_** du cluster **_mycluster_**, nous définissons les brokers de la région **eu** comme primaires et les brokers de la région **us** comme secondaires. Les brokers de la région **us** deviendront propriétaire du namespace si il y a moins de **un** broker disponible dans la région **eu**

```
docker exec -it pulsar1-eu bin/pulsar-admin ns-isolation-policy set mycluster ns-is-policy-eu --auto-failover-policy-params min_limit=1,usage_threshold=100 --auto-failover-policy-type min_available --namespaces "mytenant/eu" --secondary "pulsar.*" --primary "pulsar.*-eu"
```

Nous procédons de la même façon pour la région **_us_**

```
docker exec -it pulsar1-eu bin/pulsar-admin ns-isolation-policy set mycluster ns-is-policy-us --auto-failover-policy-params min_limit=1,usage_threshold=100 --auto-failover-policy-type min_available --namespaces "mytenant/us" --secondary "pulsar.*" --primary "pulsar.*-us"
```

Nous pouvons vérifier la configuration des politiques d'isolation
```
docker exec -it pulsar1-eu bin/pulsar-admin ns-isolation-policy list mycluster
```

Nous allons ensuite configurer la réplication synchrone des données pour chaque namespace. Nous allons choisir un **_write_quorum_** et un **_ack_quorum_** de 2 afin d'assurer la persistence des données sur chacun des datacenters grâce au placement rack-aware des bookies.

```
docker exec -it pulsar1-eu bin/pulsar-admin namespaces set-persistence --bookkeeper-ensemble 2 --bookkeeper-write-quorum 2 --bookkeeper-ack-quorum 2 -r 0 mytenant/eu
docker exec -it pulsar1-eu bin/pulsar-admin namespaces set-persistence --bookkeeper-ensemble 2 --bookkeeper-write-quorum 2 --bookkeeper-ack-quorum 2 -r 0 mytenant/us
```

Une fois tout configuré, nous redémarrons les brokers pour qu'ils appliquent bien toutes les configurations (notamment le changement de rack nécessite un reboot).
```
docker restart pulsar1-eu pulsar2-eu pulsar1-us pulsar2-us
```

#### Tests

Afin de vérifier le bon fonctionnement du cluster nous utilisons [Prometheus](https://prometheus.io/) qui va récupérer les métriques exposées par les bookies. Nous utilisons également [Grafana](https://grafana.com/) afin de visualiser les métriques sous forme de graphes.

Nous commençons d'abord par créer une souscription sur le topic **_mytopic_** du namespace **_eu_**

```
docker exec -it pulsar1-eu bin/pulsar-client --url pulsar://pulsar1-eu:6650 consume persistent://mytenant/eu/mytopic -s mysub -r 10 -n 0
```

Dans un autre terminal, nous produisons ensuite des messages sur le topic **_mytopic_**

```
docker exec -it pulsar1-eu bin/pulsar-perf produce persistent://mytenant/eu/mytopic -u http://pulsar1-eu:8080 -r 100
```

Sur Grafana, dans le [dashboard **_bookeeper_**](http://localhost:3000/dashboard/file/bookkeeper.json) nous pouvons regarder le graphique **Write throughput** afin de vérifier sur quels bookies sont persistés les données.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/produceRackAware.png)

Nous voyons ici que les données sont écrites sur les bookies **_bk1-eu_** et **_bk1-us_**, les données sont stockées sur un bookie de chaque région.

Nous pouvons également vérifier ce qui se passe lors de la consommation sur le grahique **Read throughput".

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/consumeLocal.png)

Lors de la consommation les données sont lues sur le bookie de la même région que le client et qui a persisté la donnée, ici **_bk1_eu_**.

##### Perte d'un bookie de la région active

Nous pouvons simuler la perte d'un bookie de la région active en éteignant le container **_bk1-eu_** :

```
docker stop bk1-eu
```

Le bookie n'étant plus disponible, le topic est sous-répliqué. BookKeeper possède un mécanisme d'[auto-réparation](https://bookkeeper.apache.org/docs/latest/admin/autorecovery/) qui va automatiquement répliquer les données du topic sur le nouveau bookie utilisé dans la région active **_bk2-eu_** pour rétablir le quorum d'écriture. C'est pourquoi après la perte de **_bk1-eu_** (à 13h44), on observe un pic d'écriture sur **_bk2-eu_** et un pic de lecture sur **_bk1-us_**. 
![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/perteBK1_write.png)

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/pertebk1_read.png)

Pendant le temps de l'auto-réparation, le client consomme les messages sur **_bk1-us_**. Une fois que **_bk2-eu_** a répliqué les données, le client consomme les messages sur ce dernier.

##### Perte d'un datacenter complet

Nous pouvons simuler la perte d'un datacenter en éteignant tous les containers d'un datacenter :

```
docker stop bk1-eu bk2-eu pulsar1-eu pulsar2-eu
```

Comme il n'y a plus assez de brokers pour la politique d'isolation configurée (min_limit=1) pour le namespace **eu**, Pulsar va basculer sur les brokers de la région **us**. Un des brokers de la région **us** est choisi comme propriétaire du topic. Pour assurer le quorum d'écriture de 2, les données sont persistées sur les 2 bookies de la région **us**.

##### Nettoyage

A la fin des tests, nous pouvons supprimer le cluster
```
docker-compose -f docker-compose_sync.yml down
docker-compose -f docker-compose_zk.yml down
```

## Comment mettre en place la geo-réplication asynchrone avec Pulsar ?

### Présentation

La [géo-réplication](https://pulsar.apache.org/docs/en/administration-geo/) est une réplication asynchrone des messages entre clusters d'une instance Pulsar. Elle permet aux consommateurs d'un cluster de recevoir les messages produits sur un autre cluster.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/GeoReplication.png)

Sur ce diagramme, que ce soient les producers P1, P2 ou P3 qui produisent sur le topic T1 sur les clusters C1, C2 ou C3, les messages sont répliqués entre les différents clusters. Une fois répliqués, les consumers C1 et C2 peuvent traiter les messages sur leur cluster respectif.

Sans la géo-réplication, les consumers C1 et C2 ne seraient pas capable de traiter les messages produits par le producer P3.

La géo-réplication peut être activée entre les clusters seulement quand une configuration particulière a été ajoutée qui permet d'accorder l'accès aux différents clusters :

- **_Global Namespace_** : La réplication utilise des topics globaux, c'est-à-dire des topics appartenant à un namespace global s'étend sur plusieurs clusters.
- **_Allowed Clusters_** : La configuration du namespace global doit permettre la réplication entre les différents clusters alloués.

### Démonstration avec Docker

Nous allons construire une architecture comprenant 2 clusters avec chacun 2 brokers et 2 bookies, ainsi qu'un ZooKeeper commun.

Le cluster **_cluster-eu_** sera dédié à la région **_eu_** et le cluster **_cluster-us_** sera dédié à la région **_us_**.

Les commandes ci-dessous sont à éxécuter depuis la racine du dossier [docker](https://github.com/Cdiscount/IT-Blog/tree/master/samples/Architecture/resilient-messaging/docker).

#### Configuration

Nous commençons par créer le cluster ZooKeeper :

```
docker-compose -f docker-compose_zk.yml up -d
```

Nous créons ensuite les deux clusters Pulsar et nous les initialisons dans ZooKeeper :

```
docker exec -it zk bin/pulsar zookeeper-shell create /cluster-eu data
docker exec -it zk bin/pulsar initialize-cluster-metadata \
      --cluster cluster-eu \
      --zookeeper zk:2181/cluster-eu \
      --configuration-store zk:2181 \
      --web-service-url http://pulsar1-eu:8080 \
      --broker-service-url pulsar://pulsar1-eu:6650
docker exec -it zk bin/pulsar zookeeper-shell create /cluster-us data
docker exec -it zk bin/pulsar initialize-cluster-metadata \
      --cluster cluster-us \
      --zookeeper zk:2181/cluster-us \
      --configuration-store zk:2181 \
      --web-service-url http://pulsar1-us:8080 \
      --broker-service-url pulsar://pulsar1-us:6650
```

Nous créons les bookies et les brokers :

```
docker-compose -f docker-compose_geo.yml up -d
```

Puis nous créons un tenant **_world_**, et un namespace **_world/global_** qui sera global aux deux régions.

```
docker exec -it pulsar1-eu bin/pulsar-admin tenants create world \
  --admin-roles admin-role \
  --allowed-clusters cluster-eu,cluster-us
docker exec -it pulsar1-eu bin/pulsar-admin namespaces create world/global
docker exec -it pulsar1-eu bin/pulsar-admin namespaces set-clusters world/global \
  --clusters cluster-eu,cluster-us
```

#### Tests

Nous commençons d'abord par créer une souscription et un consommateur sur le topic **_mytopic_** sur le **_cluster-eu_** :

```
docker exec -it zk bin/pulsar-client --url pulsar://pulsar1-eu:6650 consume persistent://world/global/mytopic -s mysub -r 100 -n 0
```

Nous pouvons ensuite produire des messages sur ce topic depuis le **_cluster-eu_** et constater que les messages sont bien reçus par le consommateur. Dans un autre terminal:

```
docker exec -it pulsar1-eu bin/pulsar-perf produce persistent://world/global/mytopic -u http://pulsar1-eu:8080 -r 10
```

Arrêtons la production sur le **_cluster-eu_** et lançons de la production sur le **_cluster-us_**, les messages sont aussi reçus par le consommateur du **_cluster-eu_** :

```
docker exec -it pulsar1-us bin/pulsar-perf produce persistent://world/global/mytopic -u http://pulsar1-us:8080 -r 10
```

Nous pouvons aussi créer une souscription sur le topic **_mytopic_** sur le **_cluster-us_**

> Note: les souscriptions sur les clusters sont indépendantes, il n'y a pas de "souscription globale".
> Au moment de la publication de cet article, Pulsar 2.4.0 vient de sortir avec une fonctionnalité de [réplication des souscriptions](https://pulsar.apache.org/blog/2019/07/05/Apache-Pulsar-2-4-0/#replicated-subscription). Cela permet de basculer un consommateur sur le cluster répliqué ce qui est très pratique si perdre quelques messages (lag de réplication des messages) et avoir quelques doublons (lag de réplication des souscriptions) lors d'une bascule est acceptable. Toutefois si une consistence forte est exigée, la réplication synchrone décrite plus haut reste la seule solution.

Dans un troisième terminal:

```
docker exec -it zk bin/pulsar-client --url pulsar://pulsar1-us:6650 consume persistent://world/global/mytopic -s mysub -r 100 -n 0
```

##### Perte d'un datacenter

Nous pouvons simuler la perte d'un datacenter en éteignant tous les containers d'un datacenter :

```
docker stop bk1-eu bk2-eu pulsar1-eu pulsar2-eu
```

Suite à la perte de tout le datacenter **eu**, la consommation et la production continuent de fonctionner sur le datacenter **us**. Les messages qui sont publiés sur **us** pendant que **eu** est éteint seront répliqués quand **eu** reviendra. On peut voir que le client connecté à **eu** tente de se reconnecter en boucle.

Arrêtons la production sur le **_cluster-us_**. Puis:

```
docker start bk1-eu bk2-eu pulsar1-eu pulsar2-eu
```
Lorsque le cluster **eu** est à nouveau fonctionnel, le client se reconnecte et reçoit les messages qui avaient été publiés sur **us** pendant l'extinction.

##### Nettoyage

A la fin des tests, nous pouvons supprimer le cluster
```
docker-compose -f docker-compose_geo.yml down
docker-compose -f docker-compose_zk.yml down
```

## Réaliser un bus de messaging actif/actif à forte garantie de consistence des données

Comme nous l'avons vu, les namespaces Pulsar et les fonctionalités de `region-awareness`  permettent de fortes garanties sur la livraison des messages tout en minimisant les échanges inter-datacenters avec un cluster actif/passif. Mais pour nos besoins de messaging, il était important d'avoir une réplication active/active. Pour réaliser cela, avons donc combiné la réplication synchrone et la géo-réplication asynchrone.
Cela a plusieurs avantages:

* La réplication synchrone active/passive garantit qu'on ne perd aucun messages même en cas de perte d'un datacenter.
* Lors d'une bascule vers les noeuds passifs, les clients ne changent pas de cluster et donc pas de souscription. Il n'y a donc pas besoin d'avoir un mécanisme complexe pour retrouver l'index de lecture correspondant sur l'autre cluster.
* En mode nominal, les clients produisent et consomment sur leur propre région ce qui économise la bande-passante consommée entre les régions.
* La géo-réplication permet de recevoir tous les messages quel que soit le cluster sur lequel ils ont été produits.

Il faut toutefois noter quelques inconvénients:

* Les brokers passifs peuvent être considérés comme une resource provisionnée mais inutilisée. Toutefois ces resources n'ont besoin d'être démarrées en permanence que si l'on cherche le maximum de disponibilité. Si une perte momentannée de disponibilité est acceptable en cas de bascule, on peut envisager de ne démarrer ces brokers que quand une bascule est détectée. On peut même utiliser des resources payées à l'utilisation dans le Cloud qui ne seront utilisées que pendant la bascule.
* Puisqu'on ne valide un message produit que lorsqu'il a été répliqué sur l'autre région, cela introduit une latence à l'écriture. Cette latence additionnelle peut-être un frein pour certaines applications et il faudra alors choisir entre une consistence très forte des données et la performance d'écriture.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/activeActive.png)

En cas de perte de la région EU, la bascule se fait automatiquement vers la région US:

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/basculePulsar.png)

## Conclusion

Comme nous l'avons vu, les fonctionnalités de réplication synchrone, d'isolation de namespace et de géo-réplication permettent de mettre en place un bus de messaging hautement résilient ce qui n'est pas réalisable actuellement avec les technologies concurrentes.
Si l'on ajoute la possibilité de [mutualiser les usages de diffusion d'événements et de queueing avec une unique technologie](https://streaml.io/blog/pulsar-streaming-queuing), les [fonctionnalités de traitement de flux temps réel](https://pulsar.apache.org/docs/fr/functions-overview/), la possibilité d'utiliser du [stockage à plusieurs niveaux](https://pulsar.apache.org/docs/fr/cookbooks-tiered-storage/) pour réduire les coûts, etc... cela fait de Pulsar un candidat sérieux dans la course aux bus de messages.
