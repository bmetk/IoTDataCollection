# Importing Data to InfluxDB with Telegraf

Telegraf is a data transfer agent developed by InfluxData. It can collect and output measurement data to multiple sources. To establish connections, Telegraf uses plugins which can be configured to specific needs. Ultimately, you can implement custom plugins for your data transfer.

### Plugins
There are four types of plugins in Telegraf: Input, Output, Aggregators and Processors. Each has a github page for documentation and examples. For detailed description of the plugin types please see the official [documentation](https://docs.influxdata.com/telegraf/v1.26/configure_plugins/).

- **Input plugins**: Connects the Telegraf agent to the data sources. These can be MQTT brokers, files, databases and so on.
- **Output plugins**: Specifies the output destinations and metrics for the incoming data.
- **Aggregator plugins**: Creates aggregate metrics from your data (e.g. statistics).
- **Processor plugins**: Can be used to transform, filter your metrics.

Telegraf’s config file also contains additional fields, such as the agent configuration.

## Configuring Telegraf
### Agent
First, let’s go through the agent configuration. There are a few parameters that can be configured, the most importants being the *interval* and the *flush_iterval*. These two determine the frequency of the input reading and output writing. It’s a good practice to activate some *jitter* so that the sources dont get overwhelmed. The other parameters can be found in the official [documentation](https://docs.influxdata.com/telegraf/v1.26/configuration/).

An example agent section:

```conf
[agent]
  interval = "1s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "5s"
  flush_jitter = "0s"
  precision = ""
```

### Inputs
Telegraf can be configured to connect to our Mosquitto broker container to retrieve the data we send. For this purpose we can use an input plugin called *mqtt_consumer*. Here the most important parameters are the *server* (address of the broker), *topics* (the topics we wish to subscribe to) and the *data_format*. Many data formats are supported such as value (int, float, string, boolean) and JSON.

#### Input parsing:
With the help of topic and payload parsing you can shape the incoming data. This is great for separating different measurements, add descriptive tags and use them for filtering and so on. When there is a measurement, Telegraf uses the topic for the name. However, this can be too long and not that descriptive. Let’s see a simple example for extracting these parameters given the following topic:

```
bmetk/john/lathe/vibration/mpu/vibX
```
To extract the measurement name and the tags, we can use the following syntax:

```
measurement = “_/_/measurement/_/_/_”
tags = “_/student/_/aspect/sensor/variable”
```

Now we have a measurement name of *lathe* and four tags with the key-value pairs of *student-john*, *aspect-vibration* and so on (read more about [topic and payload parsing](https://www.influxdata.com/blog/mqtt-topic-payload-parsing-telegraf/)).

An example input plugin that accepts float values from the listed topics (note the usage of wildcards) and parses the topic:

```conf
[[inputs.mqtt_consumer]]
  servers = ["tcp://mosquitto:1883"]
  topics = ["bmetk/+/+/current/#", 
            "bmetk/+/+/speed/#", 
            "bmetk/+/+/temperature/#"]
  qos = 0
  connection_timeout = "20s"
  data_format = "value"
  data_type = "float"

  [[inputs.mqtt_consumer.topic_parsing]]
    topic = "bmetk/+/+/+/+/+"
    measurement = "_/_/measurement/_/_/_"
    tags = "org/student/_/aspect/sensor/_"
```


### Outputs
Since we are using one of the newer versions of InfluxDB, the output plugins are configured to the *influxdb_v2* destination. Here you can specify what data should end up in your bucket(s) with parameters such as *namepass/namedrop*, *tagpass/tagdrop* and so on (read more about [metric filtering](https://docs.influxdata.com/telegraf/v1.26/configuration/)). Measurement names are needed to specify your metrics and can’t be left out. There is only one measurement name. Tags however are optional but can help to provide metadata and aid with further data manipulation. You can create as many tags as you want.

**Namepass/namedrop**: At the input parsing level, each metric is assigned a measurement name (default is the whole topic). The namepass parameter defines the names of the metrics we wish to output to our bucket, everything else will be left out. The namedrop is the inverse of namepass. Note that these parameters are defined at the beginning of the plugin.

**Tagpass/tagdrop**: In many cases namepass is too broad and we need more refined filtering. For this we can use tagpass/tagdrop. These are located at the end of the output plugins. In contrast to namepass, we define the tag vales for the keys we create at the parsing stage.

You can create multiple outputs for different buckets. Each output has the URL of the database and a token that allows data bucket modification. Every user should create own tokens so no accidental writes can occur.

An example output plugin that outputs metrics with the name *lathe* and tag *john* to the *destbucket* bucket:

```conf
[[outputs.influxdb_v2]]
  namepass = "lathe"
  urls = ["http://influxdb:8086"]
  token = "$INFLUX_TOKEN_THESIS"
  organization = "$DOCKER_INFLUXDB_INIT_ORG"
  bucket = "destbucket"
  
  [outputs.influxdb_v2.tagpass]
    student = ["john"]
```

## Topic structure

For simplicity, lets define a general topic structure. Remember that this will contain our measurement name and tags. Alternatively these can be changed in the plugins.

Every topic should look like the following:

```
organization / student id / asset / aspect / sensor / variable
```
where:
- *organization (org)*:   name of the InfluxDB organization
- *student id*:           name to identify the students
- *asset*:                machinery type where the data is collected from
- *aspect*:               the parameter being monitored
- *sensor*:               name of the sensor to separate same aspects (e.g. vibration)
- *variable*:             the name of the data that is collected

and the aspects are:
- current
- speed
- temperature
- vibration

An example that follows this scheme can be found at the [Input parsing](#Input-parsing) section.

## Manage configuration using the InfluxDB UI
There are different ways to create a configuration file for Telegraf, for now let's stick to InfluxDB's UI. To do that, click the *Load Data* icon on the left menu strip and navigate to the *Telegraf* tab. Here you have two options: create a new configuration or update an existing one.

**Updating can NOT be reverted!** Please be shure that your configuration works before updating. The best would be to create a new one based on the current and test it that way.

### Create new configuration
When creating a new configuration you have to select an input source (e.g. MQTT) and a bucket. These can be overwritten later. For now just give your configuration a name and a brief description and click *Finish*. You should be prompted a token and a URL for the .conf file, save these for later.

### Edit configuration
After creating a new on you can click on the name of the configuration to edit it. Paste your code here and save it. Remember that this process is irreversible. 

### Applying your configuration
Now that you have your own configuration it's time to apply it to Telegraf. The configuration requires the *INFLUX_TOKEN* you were prompted, be shure to add it to the *.env* file or export it for the Telegraf container.

To load the config into Telegraf execute the following command:

```sh
$ docker exec <container> telegraf --config http://influxdb:8086/...
```

*NOTE: You have to change the URL from localhost to InfluxDB's container name (in this case it's influxdb). Likewise change 'conatiner' to Telegraf's container name.*

### Creating tokens for Telegraf
For every output plugin that points to InfluxDB you will need an API token. You can create one in the *API tokens* section. To use it in Telegraf, select *WRITE* permission for your bucket(s) and *READ* permission for your configuration.