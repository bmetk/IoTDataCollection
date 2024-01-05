import pandas as pd
import asyncio
import websockets
 
# create handler for each connection
async def receive_messages():
    uri = "ws://172.26.0.4:8765"  # Replace with the actual WebSocket URL
    
    async with websockets.connect(uri, max_size=3000000) as websocket:
        print(f"Connected to WebSocket server @{uri}")
        while True:
            try:
                message = await websocket.recv()
                df = pd.read_json(message)
                val = [df.loc[0,'_value'], df.loc[1,'_value']]
                #print(message)
                print(df)
                print(val)
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed.")
                break


 
asyncio.get_event_loop().run_until_complete(receive_messages())
asyncio.get_event_loop().run_forever()



#df = pd.DataFrame()
#df = pd.read_json(sample_data_gen.generate_new_data(), orient="list")
#print(df)