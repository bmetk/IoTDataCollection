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
import time




router = websockets_routes.Router()
host_name = "0.0.0.0" # linux: "0.0.0.0"
combined_values = {"tempC":None, 
                    "rpm":None, 
                    "cur":None, 
                    "vibX_fft":None, "vibX_rms":None, "vibX_psd":None, 
                    "vibY_fft":None, "vibY_rms":None, "vibY_psd":None, 
                    "vibZ_fft":None, "vibZ_rms":None, "vibZ_psd":None}
analytics_deque = deque([])
data_ready = False
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
                            combined_values['tempC'] = float(message.payload.decode("utf-8"))
                            received_topics['tempC'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/rpm"):
                            combined_values['rpm'] = float(message.payload.decode("utf-8"))
                            received_topics['rpm'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/cur"):
                            combined_values['cur'] = message.payload.decode("utf-8")
                            received_topics['cur'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibX"):
                            d = await process_mqtt_payload(str(message.payload), "vibX")
                            combined_values['vibX_fft'] = d["vibX_fft"]
                            combined_values['vibX_rms'] = d["vibX_rms"]
                            combined_values['vibX_psd'] = d["vibX_psd"]
                            received_topics['vibX'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibY"):
                            d = await process_mqtt_payload(str(message.payload), "vibY")
                            combined_values['vibY_fft'] = d["vibY_fft"]
                            combined_values['vibY_rms'] = d["vibY_rms"]
                            combined_values['vibY_psd'] = d["vibY_psd"]
                            received_topics['vibY'] = True
                        if message.topic.matches("bmetk/markk/lathe/+/+/vibZ"):
                            d = await process_mqtt_payload(str(message.payload), "vibZ")
                            combined_values['vibZ_fft'] = d["vibZ_fft"]
                            combined_values['vibZ_rms'] = d["vibZ_rms"]
                            combined_values['vibZ_psd'] = d["vibZ_psd"]
                            received_topics['vibZ'] = True

                        if all(received_topics.values()):
                            data_ready = True
                            for key in received_topics.keys():
                                received_topics[key] = False        
                    

        except aiomqtt.MqttError as error:
            logging.error(f"There was an error with the client: {error}")
            await asyncio.sleep(reconnect_interval)



active_connections = set()
async def send_message(payload):
    connections_copy = active_connections.copy()
    for websocket in connections_copy:
        try:
            await websocket.send(payload)
            #logging.error("Data sent")
        except websockets.exceptions.WebSocketException as e:
            print(f"Error sending message: {e}")
            active_connections.remove(websocket)
            logging.error(f"WebSocket connection closed, remaining connections: {len(active_connections)}")


last_entry_time = 0
toggle_source = 'realtime'
send_generated = True
async def realtime_handler(websocket, path):
    global data_ready
    global toggle_source
    global last_entry_time
    global send_generated

    reset = False


    active_connections.add(websocket)
    print(f"WebSocket connection established, number of clients: {len(active_connections)}")
    logging.error(f"WebSocket connection established, number of clients: {len(active_connections)}")

    

    while True:
        try:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.2)
                previous_state = toggle_source
                toggle_source = message
                if previous_state != toggle_source:
                    reset = True
                print(toggle_source)
                logging.error(f"message: {message}, source: {toggle_source}")
            except asyncio.TimeoutError:
                pass

            if toggle_source == 'realtime' and data_ready:
                data_ready = False
                logging.error("sending real-time payload")
                payload = assemble_payload(combined_values)
                await send_message(payload)

            
            elif toggle_source == 'generated' and send_generated:
                send_generated = False
                payload = sample_data_gen.generate_combined_data(10, reset)
                reset = False
                logging.error("sending generated payload")
                await send_message(payload)
                await asyncio.sleep(2)
                send_generated = True
            
            """elif toggle_source == 'generated':
                current_time = time.time()
                if current_time-last_entry_time >= 1:
                    last_entry_time=current_time
                    payload = sample_data_gen.generate_combined_data(10, reset)
                    reset = False
                    logging.error("sending generated payload")
                    await send_message(payload)
                    await asyncio.sleep(2)"""

                
              

            #await asyncio.sleep(0.2)
        except websockets.exceptions.ConnectionClosedError:
            active_connections.remove(websocket)
            logging.error(f"WebSocket connection closed, remaining connections: {len(active_connections)}")



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
    global analytics_decue

    for key, value in values.items():
        entry = {
            "table": 0,
            "_time": str(datetime.today()) + "+00:00",
            "_value": value,
            "variable": key,
        }
        if len(analytics_deque) >= len(values)*10:
            analytics_deque.pop()
        analytics_deque.appendleft(entry)

    an_list = list(analytics_deque)

    return json.dumps(an_list, indent=2)



async def main():
    # create a WebSocket server
    server_realtime = await websockets.serve(realtime_handler, host=host_name, port=8765, ping_interval=None)

    # create and run the MQTT client in parallel with the WebSocket servers
    mqtt_task = asyncio.create_task(mqtt_client())
    await asyncio.gather(mqtt_task, server_realtime.wait_closed())


if __name__ == '__main__':
    # for windows plattform
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    asyncio.run(main())