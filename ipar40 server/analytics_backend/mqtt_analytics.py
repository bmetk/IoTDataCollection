import asyncio
import aiomqtt
import credentials as cred
import logging
import influx_write
import analytics
import sys
import os
import json
from datetime import datetime
from collections import deque
import websockets
import websockets_routes
import sample_data_gen




router = websockets_routes.Router()
host_name = "127.0.0.1" # linux: "0.0.0.0"
home_values = {"tempC":None, "rpm":None, "cur":None, "vibX_fft":None, "vibY_fft":None, "vibZ_fft":None}
analytics_values = {"tempC":None, 
                    "rpm":None, 
                    "cur":None, 
                    "vibX_rms":None, "vibX_psd":None, 
                    "vibY_rms":None, "vibY_psd":None, 
                    "vibZ_rms":None, "vibZ_psd":None}
combined_values = {"tempC":None, 
                    "rpm":None, 
                    "cur":None, 
                    "vibX_fft":None, "vibX_rms":None, "vibX_psd":None, 
                    "vibY_fft":None, "vibY_rms":None, "vibY_psd":None, 
                    "vibZ_fft":None, "vibZ_rms":None, "vibZ_psd":None}
analytics_deque = deque([])
data_ready = [False, False]
data_cnt = 10
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
    global data_ready
    global data_cnt
    global home_values
    global analytics_values
    global data_ready
    global received_topics

    while True:
        try:
            async with aiomqtt.Client(hostname=cred.mqtt_addr, port=cred.mqtt_port, username=cred.mqtt_usr, password=cred.mqtt_pwd, client_id="python-mqtt-101") as client:
                async with client.messages() as messages:
                    await client.subscribe(cred.mqtt_topic)

                    
                    
                    async for message in messages:
                        if message.topic.matches("bmetk/markk/lathe/+/+/tempC"):
                            home_values['tempC'] = float(message.payload.decode("utf-8"))
                            analytics_values['tempC'] = home_values['tempC']
                            received_topics['tempC'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/rpm"):
                            home_values['rpm'] = float(message.payload.decode("utf-8"))
                            analytics_values['rpm'] = home_values['rpm']
                            received_topics['rpm'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/cur"):
                            home_values['cur'] = message.payload.decode("utf-8")
                            analytics_values['cur'] = home_values['cur']
                            received_topics['cur'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibX"):
                            d = await process_mqtt_payload(str(message.payload), "vibX")
                            home_values['vibX_fft'] = d["vibX_fft"]
                            analytics_values['vibX_rms'] = d["vibX_rms"]
                            analytics_values['vibX_psd'] = d["vibX_psd"]
                            received_topics['vibX'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibY"):
                            d = await process_mqtt_payload(str(message.payload), "vibY")
                            home_values['vibY_fft'] = d["vibY_fft"]
                            analytics_values['vibY_rms'] = d["vibY_rms"]
                            analytics_values['vibY_psd'] = d["vibY_psd"]
                            received_topics['vibY'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibZ"):
                            d = await process_mqtt_payload(str(message.payload), "vibZ")
                            home_values['vibZ_fft'] = d["vibZ_fft"]
                            analytics_values['vibZ_rms'] = d["vibZ_rms"]
                            analytics_values['vibZ_psd'] = d["vibZ_psd"]
                            received_topics['vibZ'] = True

                        if all(received_topics.values()):
                            #print(data_cnt)
                            #data_cnt += 1
                            data_ready = [True, True]
                            for key in received_topics.keys():
                                received_topics[key] = False        
                    

        except aiomqtt.MqttError as error:
            logging.error(f"There was an error with the client: {error}")
            await asyncio.sleep(reconnect_interval)






active_home = set()
async def send_home(payload):
    connections_copy = active_home.copy()
    for websocket in connections_copy:
        try:
            await websocket.send(payload)
            #print(f"Data sent to client id: {websocket}")
        except websockets.exceptions.WebSocketException as e:
            print(f"Error sending message to /home: {e}")
            active_home.remove(websocket)
            print(f"WebSocket connection removed from /home, remaining connections: {len(active_home)}")


@router.route("/home")
async def home_handler(websocket, path):
    global data_ready
    global home_values
    global received_topics
    active_home.add(websocket)  # Add the new connection to the set
    print(f"WebSocket connection established, number of clients: {len(active_home)}")
    while True:
        # payload = sample_data_gen.generate_new_data()
        if data_ready[0]:
            data_ready[0] = False
            try:
                payload = assemble_payload(home_values)
                await send_home(payload)
                print("Data sent to /home")
                #payload = sample_data_gen.generate_new_data()
                #await websocket.send(payload)
            except websockets.exceptions.WebSocketException as e:
                print(f"Error in /home: {e}")

        await asyncio.sleep(0.2)



active_analytics = set()
async def send_analytics(payload):
    connections_copy = active_analytics.copy()
    for websocket in connections_copy:
        try:
            await websocket.send(payload)
            #print(f"Data sent to client id: {websocket}")
        except websockets.exceptions.WebSocketException as e:
            print(f"Error sending message to /home: {e}")
            active_analytics.remove(websocket)
            print(f"WebSocket connection removed from /analytics, remaining connections: {len(active_analytics)}")

@router.route("/analytics")
async def analytics_handler(websocket, path):
    global data_cnt
    global data_ready
    global analytics_values
    active_analytics.add(websocket)  # Add the new connection to the set
    print(f"WebSocket connection established, number of clients: {len(active_analytics)}")
    while True:
        # payload = sample_data_gen.generate_new_analytics()
        if data_ready[1]:
            data_ready[1] = False
            try:
                payload = assemble_analytics(analytics_values)
                await send_analytics(payload)
                #payload = sample_data_gen.generate_new_analytics()
                #await websocket.send(payload)
                print("Data sent to /analytics")
            except websockets.exceptions.WebSocketException as e:
                #print(f"Error in /analytics: {e}")
                pass

        await asyncio.sleep(0.2)





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
    #print(values)

    for key, value in values.items():
        entry = {
            "_value": value,
            "variable": key,
        }

        data.append(entry)

    return json.dumps(data, indent=2)

def assemble_analytics(values : dict) -> str:
    global analytics_decue

    for key, value in values.items():
        entry = {
            "table": 0,
            "_time": str(datetime.today()) + "+00:00",
            "_value": value,
            "variable": key,
        }
        #print(entry)
        if len(analytics_deque) >= len(values)*10:
            analytics_deque.pop()
        analytics_deque.appendleft(entry)

    an_list = list(analytics_deque)
    #print(an_list)
    #print(len(an_list))

    return json.dumps(an_list, indent=2)







async def main():
    # Create a WebSocket server
    server_home = await websockets.serve(home_handler, host=host_name, port=8764, ping_interval=None)
    server_analytics = await websockets.serve(analytics_handler, host=host_name, port=8766, ping_interval=None)

    # Create and run the MQTT client in parallel with the WebSocket servers
    mqtt_task = asyncio.create_task(mqtt_client())
    await asyncio.gather(mqtt_task, server_analytics.wait_closed()), server_home.wait_closed()

if __name__ == '__main__':
    #for windows plattform
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())


    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    asyncio.run(main())