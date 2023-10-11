import logging
import influxdb_client
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from credentials import influxhost, token, org, bucket


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



async def writeToDB(topic: str, aspects : list, values : list, fields : list) -> None:
   
    async with InfluxDBClientAsync(url=influxhost, token=token, org=org) as client:
        write_api = client.write_api()
        component = topic.split('/')

        for aspect, value, field in zip(aspects, values, fields):
            point = influxdb_client.Point(component[2]) \
                .tag("org", component[0]) \
                .tag("student", component[1]) \
                .tag("aspect", component[3]) \
                .tag("sensor", component[4]) \
                .tag("variable", field) \
                .field("value", value)
            
            try:
                successfully0 = await write_api.write(bucket=bucket, record=point)
                logging.info(f"Data successfully written to {bucket}.")
            except:
                logging.error(f"Unable to write to {bucket}. Check syntax and write parameters.")
                print("error")