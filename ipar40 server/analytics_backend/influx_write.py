import logging
import influxdb_client
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from credentials import influxhost, token, org, bucket


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



async def writeAnalyticsToDB(topic: str, aspects : list, values : list, fields : list) -> None:
   
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



async def writeEverythingToDB(data : dict) -> None:
   
    async with InfluxDBClientAsync(url=influxhost, token=token, org=org) as client:
        write_api = client.write_api()
        component = []
        

        for key in data:
            if "tempC" in key: 
                component = "bmetk/markk/lathe/temperature/mlx90614/tempC".split('/')
            if "rpm" in key:
                component = "bmetk/markk/lathe/speed/m0c70t3/rpm".split('/')
            if "cur" in key:
                component= "bmetk/markk/lathe/current/ampmeter/amp".split('/')
                component[2] = component[2] + "_strings"
            if key == "vibX" or key == "vibY" or key == "vibZ":
                component= "bmetk/markk/lathe/vibration/mpu9250".split('/')
                component[2] = component[2] + "_strings"
            if "fft" in key or "psd" in key or "rms" in key:
                component = "bmetk/markk/lathe_analytics/vibration/backend".split('/')

            point = influxdb_client.Point(component[2]) \
                .tag("org", component[0]) \
                .tag("student", component[1]) \
                .tag("aspect", component[3]) \
                .tag("sensor", component[4]) \
                .tag("variable", key) \
                .field("value", data[key])


            
            try:
                successfully0 = await write_api.write(bucket=bucket, record=point)
                logging.info(f"Data successfully written to {bucket}.")
            except:
                logging.error(f"Unable to write to {bucket}. Check syntax and write parameters.")
                print("error")