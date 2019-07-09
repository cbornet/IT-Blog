---
layout: post
title: "How Apache Pulsar allows to create a resilient messaging system"
author:
categories:
image:
---

_Grégory Guichard, R&D Engineer at Cdiscount_ <br>
_Romain Castagnet, DevOps Engineer at Cdiscount_ <br>
_Christophe Bornet, R&D Manager at Cdiscount_

At Cdiscount, we process large volumes of real-time data through distributed messaging systems. For our event broadcasting needs, we currently use [Kafka](https://kafka.apache.org/ "Kafka") and for our queuing needs, we use [RabbitMQ](https://www.rabbitmq.com/ "RabbitMQ"). Due to the nature of the data processed by Cdiscount (orders, payments, etc ...), it is imperative to guarantee a very strong consistency of the data (no duplicates, no lost messages) with the greatest possible availability, even in case of sudden loss of one of our data centers. We had difficulties to guarantee this level of requirement with Kafka and RabbitMQ and this led us to evaluate [Apache Pulsar](https://pulsar.apache.org/), the latest technology that appeared recently and which highlights strong promises in this area.

Prerequisites for testing: This blog uses [docker](https://docs.docker.com/install/) and [docker-compose](https://docs.docker.com/compose/install/) to simply start cluster nodes in isolated containers.

## What is Pulsar?

Apache Pulsar is an open-source distributed messaging solution originally created by Yahoo and now part of the Apache Software Foundation.

### Architecture

In the architecture of Pulsar, we find three components:

- **Broker** : A stateless component that processes client requests through the Pulsar protocol or a websocket proxy. It also has a REST API for administration operations.
- **[BookKeeper](https://bookkeeper.apache.org/)** : a distributed, scalable, high-performance and fault-tolerant storage. Pulsar uses BookKeeper to persist the data. A BookKeeper cluster is made up of several nodes called bookies.
- **[Zookeeper](https://zookeeper.apache.org/)** : a service that coordinates brokers and BookKeeper and stores metadata.

![](https://static1.squarespace.com/static/56894e581c1210fead06f878/t/5bb4bfb271c10b7ebdf3ca8e/1538572215597/PulsarBkZkCluster.png?format=750w)

- **Topic** : structure in which messages are published and consumed. In Pulsar or Kafka, topics are persisted so messages do not need to be consumed as soon as they are published and many consumers can read the same messages at different indexes and speeds.
- **Namespace** : allows to configure the topics policy that it will contain (retention, ACL, persistence, etc.)
- **Tenant** : Pulsar is multi-tenant, each tenant having its own authentication and authorization scheme. A tenant can contain multiple namespaces.

### Why are we interested in Pulsar?

Pulsar has several features that make it unique compared to other messaging systems:

- **Event delivery but also Message Queue** : By allowing multiple consumer groups to have their own index on the message queue, Pulsar allows event broadcasting uses on the same principle as Kafka. But Pulsar can also validate the processing of messages individually without blocking the message queue (or partition) which is not supported by Kafka and it is essential for use as queuing system.

- **Synchronous replication** : Synchronous replication is provided by BookKeeper and ensures the durability of messages even in case of loss of bookies. The rack-awareness feature ensures that messages are not acknowledged until they are written to nodes in separate data centers.

- **Native asynchronous replication** : Asynchronous replication is directly integrated into the open-source solution and is not part of a paid offer. It replicates messages between separate clusters. It should be noted that consumer reading indexes are local to a cluster and it is difficult to switch a consumer to a replicated cluster by taking it back to the correct index.

- **Simplified scalability** : Since brokers are stateless, it is very simple to add nodes to the cluster and even to auto-scaling. The system of ledgers and distribution of partitions on several nodes makes it possible to dynamically add bookies to the BookKeeper cluster without the delicate task of rebalancing the partitions.

- **Region isolation** : The cluster can be configured so that message consumptions only involve nodes in a single region in nominal mode with a failover on nodes in another region in the event of a problem. More details below.

## How to set up an active / passive cluster in synchronous replication with Pulsar?

### Presentation

We will implement an extended Pulsar cluster on 2 regions/datacenters with an active datacenter and a passive that is used only in case of active datacenter failure. In nominal mode, clients consume on the same datacenter as themselves, which reduces latency and the expensive inter-datacenter bandwidth.

1. Pulsar is configured so that the brokers chosen for the partitions of a topic are on a single datacenter.
2. A client publishes data on this topic.
3. The data is persistently synchronized on at least one bookie of the active datacenter and at least one bookie of the passive data center. Thus in case of loss of the active datacenter, the data will always be available on the second datacenter without the possibility of losing messages.
4. During the consumption, the client connects to the broker owner of the topic, this broker will preferentially read the data on a bookie of the same region as him.

In the event of active data center failure, passive data center brokers automatically become usable for publishing/consuming messages. Since there is only one Pulsar cluster, the failvoer is transparent to the clients.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/images/namespace_isolation.png)

Several configurations must be set up in order to set up a synchronous active/passive Pulsar:

- **_Namespace Isolation Policy_**: allows to isolate a namespace on a set of brokers. This ensures that brokers that own partitions are chosen primarily on a region. If there are not enough nodes available on this region (eg in case of incident) then the brokers of the other region can be chosen.
- **_Rack Awareness_** : allows messages to be replicated synchronously on bookies belonging to different racks.
- **_Region Awareness_** : allows messages to be replicated synchronously on bookies from different regions.
- **_Read reordering_** : allows to privilege the reading of the messages on bookies belonging to the same region as the broker (when the functionality Region Awareness is used)

### Demonstration with Docker

We will build an architecture with 2 datacenters, with 2 brokers and 2 bookies on each one, as well as 1 common ZooKeeper.

The first datacenter represents the region where there will be 2 brokers and 2 bookies which will be prefixed by eu. We will find the same configuration on the second datacenter that represents the us region.

On each region, we create a namespace in active configuration and another one in passive mode.

The commands below are executed from the root of the [docker] folder (./ docker).

#### Configuration

We start by creating the ZooKeeper cluster:

```
docker-compose -f docker-compose_zk.yml up -d
```

We then create the cluster **_mycluster_** in ZooKeeper :

```
docker exec -it zk bin/pulsar initialize-cluster-metadata \
      --cluster mycluster \
      --zookeeper zk:2181 \
      --configuration-store zk:2181 \
      --web-service-url http://pulsar1-eu:8080 \
      --broker-service-url pulsar://pulsar1-eu:6650
```

Then we create brokers and bookies :

```
docker-compose -f docker-compose_sync.yml up -d
```

Then we have to define the regions and racks on which bookies and brokers will be placed thanks to the **_set-bookie-rack_** command.

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

We can check the region assigned to each bookie with the command:

```
docker exec -it pulsar1-eu bin/pulsar-admin bookies racks-placement
```

We then create a tenant **_mytenant_**, and two namespaces **_mytenant/eu_** and **_mytenant/us_** that will be specific to each region.

```
docker exec -it pulsar1-eu bin/pulsar-admin tenants create mytenant \
  --admin-roles admin-role \
  --allowed-clusters mycluster
docker exec -it pulsar1-eu bin/pulsar-admin namespaces create mytenant/eu
docker exec -it pulsar1-eu bin/pulsar-admin namespaces create mytenant/us
```

We then define a namespace isolation policy for each region. For the namespace **_mytenant/eu_** of cluster **_mycluster_**, we define the brokers of the **eu** region as primary and the brokers of the **us** region as secondary. Brokers from the **us** region will become the owner of the namespace if there is less than **one** broker available in the **eu** region.

```
docker exec -it pulsar1-eu bin/pulsar-admin ns-isolation-policy set mycluster ns-is-policy-eu --auto-failover-policy-params min_limit=1,usage_threshold=100 --auto-failover-policy-type min_available --namespaces "mytenant/eu" --secondary "pulsar.*" --primary "pulsar.*-eu"
```

We proceed in the same way for the **us** region

```
docker exec -it pulsar1-eu bin/pulsar-admin ns-isolation-policy set mycluster ns-is-policy-us --auto-failover-policy-params min_limit=1,usage_threshold=100 --auto-failover-policy-type min_available --namespaces "mytenant/us" --secondary "pulsar.*" --primary "pulsar.*-us"
```

We can check the configuration of the isolation policies

```
docker exec -it pulsar1-eu bin/pulsar-admin ns-isolation-policy list mycluster
```

We will then configure synchronous data replication for each namespace. We will choose a **_write_quorum_** and an **_ack_quorum_** of 2 to ensure the persistence of the data on each of the data centers thanks to the rack-aware placement of the bookies.

```
docker exec -it pulsar1-eu bin/pulsar-admin namespaces set-persistence --bookkeeper-ensemble 2 --bookkeeper-write-quorum 2 --bookkeeper-ack-quorum 2 -r 0 mytenant/eu
docker exec -it pulsar1-eu bin/pulsar-admin namespaces set-persistence --bookkeeper-ensemble 2 --bookkeeper-write-quorum 2 --bookkeeper-ack-quorum 2 -r 0 mytenant/us
```

Once everything is configured, we restart the brokers so that they apply all the configurations (in particular the change of rack requires a reboot).

```
docker restart pulsar1-eu pulsar2-eu pulsar1-us pulsar2-us
```

#### Tests

In order to verify the proper functioning of the cluster we use [Prometheus](https://prometheus.io/) which will recover the metrics exposed by the bookies. We also use [Grafana](https://grafana.com/) to visualize metrics as graphics.

We first start by creating a subscription on topic **_mytopic_** of the **eu** namespace

```
docker exec -it pulsar1-eu bin/pulsar-client --url pulsar://pulsar1-eu:6650 consume persistent://mytenant/eu/mytopic -s mysub -r 10 -n 0
```

In another terminal, we then produce messages on the topic **_mytopic_**

```
docker exec -it pulsar1-eu bin/pulsar-perf produce persistent://mytenant/eu/mytopic -u http://pulsar1-eu:8080 -r 100
```

On [Grafana], in the [dashboard **_bookeeper_**](http://localhost:3000/dashboard/file/bookkeeper.json), we can look at the graph **Write throughput** to check on which bookies are persisted the data.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/images/produceRackAware.png)

We see here that the data are written on the bookies **_bk1-eu_** and **_bk1-us_**, the data are stored on a bookie of each region.

We can also check what happens during consumption on the graph **Read throughput**.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/images/consumeLocal.png)

During the consumption the data are read on the bookie of the same region as the customer and which persisted the data, here **_bk1_eu_**.

##### Loss of a bookie from the active region

We can simulate the loss of a bookie of the active region by turning off the container **_bk1-eu_** :

```
docker stop bk1-eu
```

The bookie is no longer available, the topic is under-replicated. BookKeeper has a [self-healing](https://bookkeeper.apache.org/docs/latest/admin/autorecovery/) mechanism that will automatically replicate the topic data on the new bookie used in the active region **_bk2-eu_** to restore the write quorum. This is why after the loss of **_bk1-eu_** (at 13:44), we observe a peak of writing on **_bk2-eu_** and a peak of reading on **_bk1-us_**.
![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/images/perteBK1_write.png)

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/images/pertebk1_read.png)

During the time of self-healing, the client consumes the messages on **_bk1-us_**. Once **_bk2-eu_** replicates the data, the client consumes the messages on it.

##### Loss of a complete data center

We can simulate the loss of a datacenter by turning off all the containers in a datacenter:

```
docker stop bk1-eu bk2-eu pulsar1-eu pulsar2-eu
```

Since there are not enough brokers for the configured isolation policy (min_limit = 1) for the **eu** namespace, Pulsar will switch to the brokers of the **us** region. One of the brokers in the **us** area is chosen as the owner of the topic. To ensure the write quorum of 2, the data are persisted on the 2 bookies of the **us** region.

##### Cleaning

At the end of the tests, we can remove the cluster

```
docker-compose -f docker-compose_sync.yml down
docker-compose -f docker-compose_zk.yml down
```

## How to set up asynchronous geo-replication with Pulsar?

### Presentation
[Georeplication](https://pulsar.apache.org/docs/en/administration-geo/) is an asynchronous replication of messages between clusters of a Pulsar instance. It allows consumers in one cluster to receive messages produced on another cluster.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/images/GeoReplication.png)

In this diagram, whether the producers P1, P2 or P3 produce on the topic T1 on clusters C1, C2 or C3, the messages are replicated between the different clusters. Once replicated, consumers C1 and C2 can process the messages on their respective cluster.

Without geo-replication, the C1 and C2 consumers would not be able to process the messages produced by the producer P3.

Geo-replication can be enabled between clusters only when a particular configuration has been added that allows access to different clusters:

- **_Global Namespace_** : Replication uses global topics, that is, topics belonging to a global namespace span multiple clusters.
- **_Allowed Clusters_** : The configuration of the global namespace must allow replication between the allocated clusters.

### Demonstration with Docker

We will build an architecture including 2 clusters with 2 brokers and 2 bookies, as well as a common ZooKeeper.

The cluster **_cluster-eu_** will be dedicated to the **eu** region and the cluster **_cluster-us_** will be dedicated to the **us** region.

The commands below are executed from the root of the [docker] folder (./ docker).

#### Configuration

We start by creating the ZooKeeper cluster:

```
docker-compose -f docker-compose_zk.yml up -d
```

We then create the two Pulsar clusters and initialize them in ZooKeeper:

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

We create bookies and brokers:

```
docker-compose -f docker-compose_geo.yml up -d
```

Then we create a **_world_** tenant, and a **_world/global_** namespace that will be global to both regions.

```
docker exec -it pulsar1-eu bin/pulsar-admin tenants create world \
  --admin-roles admin-role \
  --allowed-clusters cluster-eu,cluster-us
docker exec -it pulsar1-eu bin/pulsar-admin namespaces create world/global
docker exec -it pulsar1-eu bin/pulsar-admin namespaces set-clusters world/global \
  --clusters cluster-eu,cluster-us
```

#### Tests

We first start by creating a subscription and a consumer on the topic **_mytopic_** on **_cluster-eu_**:

```
docker exec -it zk bin/pulsar-client --url pulsar://pulsar1-eu:6650 consume persistent://world/global/mytopic -s mysub -r 100 -n 0
```

We can then produce messages on this topic from the **_cluster-eu_** and find that the messages are well received by the consumer. In another terminal:

```
docker exec -it pulsar1-eu bin/pulsar-perf produce persistent://world/global/mytopic -u http://pulsar1-eu:8080 -r 10
```

Let's stop the production on the **_cluster-eu_** and launch production on the **_cluster-us_**, the messages are also received by the consumer of the **_cluster-eu_**:

```
docker exec -it pulsar1-us bin/pulsar-perf produce persistent://world/global/mytopic -u http://pulsar1-us:8080 -r 10
```

We can also create a subscription on the topic **_mytopic_** on the **_cluster-us_** (NB: the subscriptions on the clusters are independent, there is no "global subscription"). In a third terminal:

```
docker exec -it zk bin/pulsar-client --url pulsar://pulsar1-us:6650 consume persistent://world/global/mytopic -s mysub -r 100 -n 0
```

##### Loss of a datacenter

We can simulate the loss of a datacenter by turning off all the containers in a datacenter:

```
docker stop bk1-eu bk2-eu pulsar1-eu pulsar2-eu
```

Due to the loss of the entire **eu** datacenter, consumption and production continue to run on the **us** datacenter. Messages that are posted on **us** while **eu** being turned off will be replicated when **eu** comes back. It can be seen that the client connected to **eu** is trying to reconnect in a loop.

Stop production on the **_cluster-us_**. Then:

```
docker start bk1-eu bk2-eu pulsar1-eu pulsar2-eu
```

When the **eu** cluster is back up, the client reconnects and receives the messages that were posted to **us** during shutdown.

##### Cleaning

At the end of the tests, we can remove the cluster

```
docker-compose -f docker-compose_geo.yml down
docker-compose -f docker-compose_zk.yml down
```

## Create an active / active messaging bus with strong data consistency guarantee
As we have seen, Pulsar namespaces and region-awareness features provide strong guarantees for message delivery while minimizing cross-datacenter exchanges with an active/passive cluster. But for our messaging needs, it was important to have active/active replication. To achieve this, we have combined synchronous replication and asynchronous geo-replication. This has several advantages:

- Active/passive synchronous replication ensures that no messages are lost even if a datacenter is lost.
- When switching to passive nodes, clients do not change cluster and therefore their subscription. There is no need to have a complex mechanism to find the corresponding read index on the other cluster.
- In nominal mode, customers produce and consume on their own region that saves the bandwidth consumed between regions.
- Geo-replication can receive all messages regardless of the cluster on which they were produced.

However, there are some disadvantages:

- Passive brokers can be considered as a provisioned but unused resource. However, these resources only need to be started permanently if we are looking for maximum availability. If a momentary loss of availability is acceptable in the event of a failover, it is conceivable to start these brokers only when a failover is detected. You can even use paid-for-use resources in the cloud that will only be used during the failover.
- Since we only validate a message produced when it has been replicated to the other region, this introduces latency to writing. This additional latency may be a brake for some applications and it will then necessary to choose between a very strong consistency of the data and the writing performance.

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/images/activeActive.png)

In case of loss of the EU region, the switch is done automatically to the US region:

![]({{ site.baseurl }}/assets/images/Architecture/resilient-messaging/images/basculePulsar.png)

## Conclusion

As we have seen, the synchronous replication, namespace isolation and geo-replication features make it possible to set up a highly resilient messaging bus which is not currently possible with competing technologies. If we add the ability to [pool the uses of event broadcasting and queuing with a single technology](https://streaml.io/blog/pulsar-streaming-queuing), [the real-time flow processing features](https://pulsar.apache.org/docs/fr/functions-overview/) inspired by Kafka Streams, the possibility of using [multi-level storage](https://pulsar.apache.org/docs/fr/cookbooks-tiered-storage/) to reduce costs, etc. ... this makes Pulsar a serious candidate in the race of messaging system. However, Pulsar is a technology still young, with an emerging community, and with few large known users in production compared to its competitors. It should therefore be determined if its unique features justify taking the bet to put it in the center of your information system.
