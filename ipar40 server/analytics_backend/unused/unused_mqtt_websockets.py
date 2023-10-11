import asyncio
import aiomqtt
import credentials as cred
import logging
import influx_write
import analytics
import sys
import os
import json

import websockets
import websockets_routes
import sample_data_gen

import influx
import influx_query
import concurrent.futures

host_name = "localhost" # linux: "0.0.0.0"
websocket_path = ""
home_values = {"tempC":None, "rpm":None, "cur":None, "vibX_fft":None, "vibY_fft":None, "vibZ_fft":None}
data_ready = [False, False]
received_topics = {
    "tempC": False,
    "rpm": False,
    "cur": False,
    "vibX": False,
    "vibY": False,
    "vibZ": False
}

async def mqtt_client():
    reconnect_interval = 1
    global home_values
    global data_ready
    global received_topics

    while True:
        
        try:
            #async with aiomqtt.Client(hostname=cred.mqtt_addr, port=cred.mqtt_port, username=cred.mqtt_usr, password=cred.mqtt_pwd, client_id="python-mqtt-101") as client:
            async with aiomqtt.Client(hostname=cred.mqtt_addr, 
                                      port=cred.mqtt_port, 
                                      username=cred.mqtt_usr, 
                                      password=cred.mqtt_pwd, 
                                      client_id="python-mqtt-101",
                                     ) as client:
                async with client.messages() as messages:
                    await client.subscribe(cred.mqtt_topic)
                 
                    async for message in messages:
                        if message.topic.matches("bmetk/markk/lathe/+/+/tempC"):
                            home_values['tempC'] = message.payload
                            received_topics['tempC'] = True
                            print("tempC")
                        if message.topic.matches("bmetk/markk/lathe/+/+/rpm"):
                            home_values['rpm'] = message.payload
                            received_topics['rpm'] = True
                            print("rpm")

                        if message.topic.matches("bmetk/markk/lathe/+/+/cur"):
                            home_values['cur'] = message.payload
                            received_topics['cur'] = True
                            print("cur")
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibX"):
                            d = await process_mqtt_payload(str(message.payload), "vibX")
                            home_values['vibX_fft'] = d["vibX_fft"]
                            received_topics['vibX'] = True
                            print("vibX")
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibY"):
                            d = await process_mqtt_payload(str(message.payload), "vibY")
                            home_values['vibY_fft'] = d["vibY_fft"]
                            received_topics['vibY'] = True
                            print("vibY")
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibZ"):
                            d = await process_mqtt_payload(str(message.payload), "vibZ")
                            home_values['vibZ_fft'] = d["vibZ_fft"]
                            received_topics['vibZ'] = True
                            print("vibZ")

                        print("messages processed")
                        
                        if all(received_topics.values()):
                            print("ws send started")
                            await send_mqtt_over_ws(home_values)
                            for key in home_values.keys():
                                received_topics[key] = False

        except aiomqtt.MqttError as error:
            logging.error(f"There was an error with the client: {error}")
            await asyncio.sleep(reconnect_interval)


async def send_mqtt_over_ws(payload : dict):
    try:
        async with aiomqtt.Client(hostname=cred.mqtt_addr, 
                                    port=cred.mqtt_ws_port, 
                                    username=cred.mqtt_usr, 
                                    password=cred.mqtt_pwd,  
                                    client_id="python-mqtt-ws-102",
                                    transport="websockets",
                                    websocket_headers=None,
                                    websocket_path="/home") as client:
            await client.publish(topic="", payload=assemble_payload(payload))
            print("successfully sent payload with mqtt over websockets")
    except aiomqtt.MqttError as error:
        print(f"{error}")





async def process_mqtt_payload(payload : str, variable : str) -> dict:
        result = dict.fromkeys([variable+"_fft", variable+"_rms", variable+"_psd"])
    
        vib_data = analytics.string_to_array(payload)
        result[variable+"_fft"] = analytics.calculate_fft(vib_data)
        result[variable+"_rms"] = analytics.calculate_rms(vib_data)
        result[variable+"_psd"] = analytics.get_psd(vib_data)

        await influx_write.writeToDB(cred.analytics_topic,
                    ["vib_fft", "vib_rms", "vib_psd"],
                    [result[variable+"_fft"], result[variable+"_rms"], result[variable+"_psd"]],
                    [variable+"_fft", variable+"_rms", variable+"_psd"])
        
        return result



def assemble_payload(values : dict) -> str:
    data = []

    for key, value in values.items():
        entry = {
            "_value": value,
            "variable": key,
        }

        data.append(entry)

    return json.dumps(data, indent=2)



async def main():
    mqtt_task = asyncio.create_task(mqtt_client())
    await asyncio.gather(mqtt_task)
    logging.warning("MQTT and WebSocket services are up")


if __name__ == '__main__':
    #for windows plattform
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())


    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    #logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    asyncio.run(main())