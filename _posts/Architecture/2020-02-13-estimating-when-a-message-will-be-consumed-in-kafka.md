---
layout: post
title: "Estimating when a message will be consumed in Kafka"
author: christophe.bornet
categories: [en, cloud, kafka, messaging]
image: assets/images/Architecture/kafka-lag-stats/hourglass.jpg
---

At Cdiscount we use Kafka for a wide variety of applications. From a simple buffer in front of spiky workload, to the distribution of events between services, to the real-time analysis of incoming data.
During workload spikes, some consumers can't keep up with the amount of data produced and start to lag.
Monitoring the lag of the consumers is very important when operating a Kafka cluster as a lag too important is often a sign that something goes wrong. Open-source tools such as LinkedIn's [Burrow](https://github.com/linkedin/Burrow) can be used to measure the consumer lag and export it to monitoring systems such as Prometheus.

When a consumer starts to lag, we often have the following scenario : we know that a specific message has been published to Kafka at a given timestamp (eg. because it's part of an ETL pipeline and it has been tagged as processed by the previous step) and we want to know approximately when it will be consumed by a given consumer.
To do this we need to know how much messages are still to be processed before getting to our message and what is the average speed of consumption of the consumer concerned.

## Computing the number of messages that must be read by a consumer

In Kafka, messages are written to and read from topics.
When creating a topic, one can choose to spread it over a certain number of partitions.
Each partition is replicated according to the topic replication factor on a number of the Kafka cluster node. 
Kafka elects a leader node for the partition on which all reads and writes are made. Each time a message is written to the partition by a producer, Kafka increments the "end offset" of that partition.

{: style="text-align:center"}
![log_anatomy](https://kafka.apache.org/24/images/log_anatomy.png)

To consume messages, Kafka uses the concept of consumer groups.
You can have multiple consumer groups consuming a topic and each group will get all the messages from the topic.
Inside a consumer group, each consumer will be attributed one or more partitions to read from.
A consumer can read from multiple partitions but a partition can be attributed to only one consumer of a consumer group (meaning you can't have more consumers than partitions inside a consumer group).

{: style="text-align:center"}
![consumer_groups](https://kafka.apache.org/24/images/consumer-groups.png)

To know the position at which it should read new messages, an offset is maintained by Kafka for each consumer group and partition. Consumers need to regularly commit to Kafka the new offsets as they read and process new messages.

{: style="text-align:center"}
![]({{ site.baseurl }}/assets/images/Architecture/kafka-lag-stats/log_consumer2.png)

The consumer lag for a partition and consumer group is the difference between the end offset and the consumer group offset for that partition.

To get more details on topics, offsets and consumer groups, you can refer to the excellent [Kafka's documentation](https://kafka.apache.org/documentation/#intro_topics).

### Determining the partition on which a message is stored

The partition on which a message is stored is determined by the [Partitioner](https://kafka.apache.org/21/javadoc/org/apache/kafka/clients/producer/Partitioner.html) used by the publisher.
In most cases at Cdiscount, the [DefaultPartitioner](https://github.com/apache/kafka/blob/2.3.1/clients/src/main/java/org/apache/kafka/clients/producer/internals/DefaultPartitioner.java) is used which works by hashing the message's partition key if one is provided or doing a round-robin on the available partitions if no key is provided.
Kafka guarantees order over partitions and in general we want ordering of messages for a given identifier (user id, product id, order id, etc..).
So we use that identifier as the partition key and thus we can guess on which partition the message will go if we know this identifier.
If we know the number of partitions for a topic (which we can get with the [partitionsFor](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html#partitionsFor-java.lang.String-) method of a Kafka consumer), we can reuse the code from Kafka to compute the partition for the partition key:
```java
int partition = Utils.toPositive(Utils.murmur2(key.getBytes(StandardCharsets.UTF_8))) % numPartitions;
```

### Getting the partition end offset for a given timestamp

The Kafka consumer API has an [endOffsets](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html#endOffsets-java.util.Collection-) method to get the current end offset of a partition.
But what we want is to have the offset for a message which was published some time ago.
For this we need to know on which partition the message was published (see above) and the end offset of the partition at the time the message was published.
Fortunately, Kafka consumer API also has a [offsetsForTimes](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html#offsetsForTimes-java.util.Map-) method which does exactly that.

### Getting the current consumer offset for the partition

The Kafka admin API has a [listConsumerGroupOffsets](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/admin/Admin.html#listConsumerGroupOffsets-java.lang.String-) that returns the consumer offsets for all the topic partitions of a consumer group.

### Computing the number of messages that must be read before reaching a message

Once we know on which partition a message is stored, we can compute the number of messages as the difference between the partition offset at the time the message was published and the current consumer offset for the partition.

## Estimating the speed of consumption of a consumer

There are two cases regarding the speed of consumption:
* The consumer doesn't lag behind the producer: it means that the consumer is faster than the producer and the speed of consumption is the speed of the producer.
* The consumer lags behind the producer: the speed of consumption is the one of the consumer.

We can determine the speed of consumption for a lagging consumer by computing the difference of consumer offsets taken at 2 distinct timestamps and dividing it by the difference of those two timestamps.
The timestamps must be close enough to assume that the consumer didn't catch up to the producer between them (or else during the time the consumer had catched up we were measuring the speed of the producer and not the one of the consumer).

{: style="text-align:center"}
![]({{ site.baseurl }}/assets/images/Architecture/kafka-lag-stats/consumer_lag_speed.jpg)

Kafka doesn't retain the consumer offsets for a given timestamps like it does for the producer offsets.
So the strategy we used was to run a service that would snapshot the consumer offsets at regular intervals using the [listConsumerGroupOffsets](https://kafka.apache.org/24/javadoc/org/apache/kafka/clients/admin/Admin.html#listConsumerGroupOffsets-java.lang.String-) method of a Kaka admin client. Those snapshots are stored in an in-memory circular buffer.
Then we can compute the speed of consumption at a given time using these snapshots.
We then filter these speeds to only keep the ones where the consumer is lagging and compute a weighed average over a period of time.

## Estimating the time remaining before a message is consumed by a consumer

The time remaining before a message is consumed by a consumer is computed as the number of messages that the consumer must read before reaching the message divided by the speed of consumption of the consumer for the message partition.

## To conclude

We have developped an application called [kafka-lag-stats](https://github.com/Cdiscount/kafka-lag-stats) that can be connected to any Kafka cluster and that performs the regular snapshots required to compute the speed of consumption.
It also exposes an HTTP endpoint to estimate the time remaining before a message is consumed depending on the consumer group, the message partition key (or direct partition number if known), and the timestamp at which the message was published.

The code is hosted on [github](https://github.com/Cdiscount/kafka-lag-stats) and we happily welcome contributions.
We also published a docker image for quick usage:
```
docker pull cdiscount/kafka-lag-stats
```
The consumption of the message is defined by the consumer group, the topic and the partition on which the message is written.
If the partitioner used by the producer is the [DefaultPartitioner](https://github.com/apache/kafka/blob/2.3.1/clients/src/main/java/org/apache/kafka/clients/producer/internals/DefaultPartitioner.java) and the producer uses a partition key, then the kafka-lag-stats endpoints can be used by providing the partition key used for the message. Otherwise, the partition must be provided explicitly.

Example for topic `my-topic`, consumer group `my-group`, message key `my-key`:

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
