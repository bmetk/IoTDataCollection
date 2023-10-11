import asyncio
import websockets
import websockets_routes
import sample_data_gen
import influx
import influx_query

router = websockets_routes.Router()
host_name = "0.0.0.0" # linux: "0.0.0.0"


"""@router.route("/home")
async def home_handler(websocket, path):
    while True:
        #payload = await influx.get_last_element(influx_query.query_home)
        payload = sample_data_gen.generate_new_data()
        if payload != None:
            await websocket.send(payload)

        await asyncio.sleep(1)"""

@router.route("/analytics")
async def analytics_handler(websocket, path):
    while True:
        payload = await influx.get_last_n_element(influx_query.query_analytics)
        #payload = sample_data_gen.generate_new_analytics()
        if payload != None:
            await websocket.send(payload)

        await asyncio.sleep(10)



async def main():
    #server_home = await websockets.serve(home_handler, host=host_name, port=8764, ping_interval=None)
    server_analytics = await websockets.serve(analytics_handler, host=host_name, port=8766, ping_interval=None)
    await asyncio.gather(server_analytics.wait_closed())#, server_home.wait_closed(), )


if __name__ == "__main__":
    #asyncio.get_event_loop().run_until_complete(main())
    asyncio.run(main())
    