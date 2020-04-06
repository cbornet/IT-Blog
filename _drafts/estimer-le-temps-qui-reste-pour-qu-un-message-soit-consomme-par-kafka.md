---
layout: post
title: "Estimer le temps qui reste pour qu'un message soit consommé par Kafka"
author: christophe.bornet
categories: [fr, cloud, kafka, messaging]
image: assets/images/Architecture/kafka-lag-stats/hourglass.jpg
excerpt_separator: <!--end of excerpt-->
precontent: "[🇬🇧 To English version](../estimating-when-a-message-will-be-consumed-in-kafka)"
---
Chez Cdiscount, nous utilisons Kafka pour une grande variété d'applications. De la mémoire tampon pour absorber les pics de charge, à la communication d'événements entre services, à l'analyse en temps réel des données entrantes.
Pendant les pics de charge, certains consommateurs ne peuvent pas suivre la quantité de données produites et prennent du retard.
Surveiller le retard des consommateurs est très important lors de l'exploitation d'un cluster Kafka car un retard trop important est souvent le signe que quelque chose ne va pas. Des outils open source tels que [Burrow](https://github.com/linkedin/Burrow) de LinkedIn peuvent être utilisés pour mesurer le retard des consommateurs et l'exporter vers des systèmes de supervision tels que Prometheus.

Lorsqu'un consommateur commence à prendre du retard, nous avons souvent le scénario suivant: nous savons qu'un message spécifique a été publié sur Kafka à un instant donné (par exemple parce qu'il fait partie d'un traitement ETL et qu'il a été marqué comme traité par l'étape précédente) et nous voulons savoir approximativement quand il sera consommé par un consommateur donné.
Pour ce faire, nous devons savoir combien de messages doivent encore être traités avant d'arriver à notre message et quelle est la vitesse moyenne de consommation du consommateur concerné.
<!--end of excerpt-->

## Calculer le nombre de messages qui doivent être lus par un consommateur

Dans Kafka, les messages sont écrits et lus à partir des `topics`.
Lors de la création d'un topic, on peut choisir de le répartir sur un certain nombre de partitions.
Chaque partition est répliquée selon le facteur de réplication du topic sur un certain nombre de nœuds du cluster Kafka.
Kafka élit un nœud leader pour la partition sur laquelle toutes les lectures et écritures sont effectuées. Chaque fois qu'un message est écrit sur la partition par un producteur, Kafka incrémente l'"offset de fin" de cette partition.

{: style="text-align:center"}
![log_anatomy](https://kafka.apache.org/24/images/log_anatomy.png)

Pour consommer des messages, Kafka utilise le concept de groupes de consommateurs.
Vous pouvez avoir plusieurs groupes de consommateurs consommant un topic et chaque groupe recevra tous les messages du topic.
Au seing d'un groupe de consommateurs, chaque consommateur se verra attribuer une ou plusieurs partitions à lire.
Un consommateur peut lire à partir de plusieurs partitions, mais une partition ne peut être attribuée qu'à un seul consommateur d'un groupe de consommateurs (ce qui signifie que vous ne pouvez pas avoir plus de consommateurs que de partitions au seing d'un groupe de consommateurs).

{: style="text-align:center"}
![consumer_groups](https://kafka.apache.org/24/images/consumer-groups.png)

Pour connaître la position à laquelle il doit lire les nouveaux messages, un offset est maintenu par Kafka pour chaque groupe de consommateurs et partition. Les consommateurs doivent régulièrement envoyer à Kafka les nouveaux offsets lorsqu'ils lisent et traitent les nouveaux messages.

{: style="text-align:center"}
![]({{ site.baseurl }}/assets/images/Architecture/kafka-lag-stats/log_consumer2.png)

Le retard (lag) du consommateur pour une partition et un groupe de consommateurs est la différence entre l'offset de fin et l'offset du groupe de consommateurs pour cette partition.

Pour obtenir plus de détails sur les topics, les offsets et les groupes de consommateurs, vous pouvez vous référer à l'excellente [documentation de Kafka](https://kafka.apache.org/documentation/#intro_topics).

### Déterminer la partition sur laquelle un message est stocké

La partition sur laquelle un message est stocké est déterminée par le [Partitionneur](https://kafka.apache.org/21/javadoc/org/apache/kafka/clients/producer/Partitioner.html) utilisé par l'émetteur.
Dans la plupart des cas chez Cdiscount, le [DefaultPartitioner](https://github.com/apache/kafka/blob/2.3.1/clients/src/main/java/org/apache/kafka/clients/producer/internals/DefaultPartitioner.java) est utilisé, qui fonctionne en hachant la clé de partition du message si elle est fournie ou en effectuant une rotation sur les partitions disponibles si aucune clé n'est fournie.
Kafka garantit l'ordre des messages sur les partitions et en général, nous voulons ordonner les messages selon un identifiant donné (identifiant utilisateur, identifiant produit, identifiant de commande, etc...).
Nous utilisons donc cet identifiant comme clé de partition et nous pouvons donc deviner sur quelle partition ira le message si nous connaissons cet identifiant.
Si nous connaissons le nombre de partitions pour un topic (que nous pouvons obtenir avec la méthode [partitionsFor](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html#partitionsFor-java.lang.String-) d'un consommateur Kafka), nous pouvons réutiliser le code de Kafka pour calculer la partition pour la clé de partition:
```java
int partition = Utils.toPositive(Utils.murmur2(key.getBytes(StandardCharsets.UTF_8))) % numPartitions;
```

### Obtenir l'offset de fin d'une partition pour un horodatage donné

L'API des consommateurs Kafka dispose d'une méthode [endOffsets](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html#endOffsets-java.util.Collection-) pour obtenir l'offset de fin courant d'une partition.
Mais ce que nous voulons, c'est avoir l'offset pour un message qui a été publié il y a quelque temps.
Pour cela, nous devons savoir sur quelle partition le message a été publié (voir ci-dessus) et l'offset de fin de la partition au moment de la publication du message.

Heureusement, l'API des consommateurs Kafka a également une méthode [offsetsForTimes](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html#offsetsForTimes-java.util.Map-) qui fait exactement cela.

### Obtenir l'offset du consommateur actuel pour la partition

L'API d'administration Kafka a une méthode [listConsumerGroupOffsets](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/admin/Admin.html#listConsumerGroupOffsets-java.lang.String-) qui renvoie les offsets de consommateur pour toutes les partitions des topics d'un groupe de consommateurs.

### Calculer le nombre de messages à lire avant d'atteindre un message

Une fois que nous savons sur quelle partition un message est stocké, nous pouvons calculer le nombre de messages comme la différence entre l'offset de partition au moment où le message a été publié et l'offset de consommation actuel pour la partition.

## Estimer la vitesse de consommation d'un consommateur

Il y a deux cas concernant la vitesse de consommation:
* Le consommateur n'est pas en retard sur le producteur: cela signifie que le consommateur est plus rapide que le producteur et la vitesse de consommation est la vitesse du producteur.
* Le consommateur est en retard sur le producteur: la vitesse de consommation est celle du consommateur.

Nous pouvons déterminer la vitesse de consommation d'un consommateur en retard en calculant la différence des offsets de consommation pris à 2 horodatages distincts et en la divisant par la différence de ces deux horodatages.
Les horodatages doivent être suffisamment proches pour considérer que le consommateur n'a pas rattrapé le producteur entre eux (sinon pendant le temps où le consommateur avait rattrapé, nous mesurions la vitesse du producteur et non celle du consommateur).

{: style="text-align:center"}
![]({{ site.baseurl }}/assets/images/Architecture/kafka-lag-stats/consumer_lag_speed.jpg)

Kafka ne conserve pas les offsets des consommateurs pour un horodatage donné comme il le fait pour les offsets des producteurs.
La stratégie que nous avons utilisée consiste donc à exécuter un service qui enregistre les offsets des consommateurs à intervalles réguliers en utilisant la méthode [listConsumerGroupOffsets](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/admin/Admin.html# listConsumerGroupOffsets-java.lang.String-) d'un client d'administration Kafka. Ces enregistrements sont stockés dans un tampon circulaire en mémoire.
Ensuite, nous pouvons calculer la vitesse de consommation à un instant donné en utilisant ces enregistrements.
Nous filtrons les vitesses pour ne garder que celles où le consommateur est en retard et calculons une moyenne pondérée sur une période de temps.

## Estimer le temps restant avant qu'un message ne soit consommé par un consommateur

Le temps restant avant qu'un message ne soit consommé par un consommateur est calculé comme le nombre de messages que le consommateur doit lire avant d'atteindre le message divisé par la vitesse de consommation du consommateur pour la partition du message.

## Pour conclure

Nous avons développé une application appelée [kafka-lag-stats](https://github.com/cbornet/kafka-lag-stats) qui peut être connectée à n'importe quel cluster Kafka et qui effectue les enregistrements réguliers requis pour calculer la vitesse de consommation.
Il expose également un service HTTP pour estimer le temps restant avant la consommation d'un message en fonction du groupe de consommateurs, de la clé de partition du message (ou du numéro de partition s'il est connu) et de l'horodatage auquel le message a été publié.

Le code est hébergé sur [github](https://github.com/cbornet/kafka-lag-stats) et nous acceptons volontiers les contributions.
Nous avons également publié une image docker pour une utilisation rapide:
```
docker pull cdiscount/kafka-lag-stats
```
La consommation du message est définie par le groupe de consommateurs, le topic et la partition sur laquelle le message est écrit.
Si le partitionneur utilisé par le producteur est le [DefaultPartitioner](https://github.com/apache/kafka/blob/2.3.1/clients/src/main/java/org/apache/kafka/clients/producer/internals/DefaultPartitioner.java) et si le producteur utilise une clé de partition, les services HTTP de kafka-lag-stats peuvent être utilisés en fournissant la clé de partition utilisée pour le message. Sinon, le numéro de la partition doit être fourni explicitement.


Exemple pour le topic `my-topic`, le groupe de consommateurs `my-group`, et la clé de partition `my-key`:
```shell
curl "http://localhost:8080/api/kafka-lag/time-remaining?group=my-group&topic=my-topic&key=my-key&publishTimestamp=2019-11-28T10:02:57.574Z"
```

```json
{
  "partition" : 0,
  "timeRemaining" : 440.32,
  "messageLag" : {
    "consumerOffset" : 2500,
    "producerOffset" : 8004,
    "lagMessages" : 5504,
    "timestamp" : "2019-11-28T10:02:57.574Z"
  },
  "speedStats" : {
    "meanSpeed" : {
      "mean" : 12.5,
      "stddev" : 12.5,
      "stddevPercent" : 100.0
    },
```
