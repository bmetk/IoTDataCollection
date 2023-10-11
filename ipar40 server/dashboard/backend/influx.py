import asyncio
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from config import influxhost, token, org, bucket

import influx_query

#-------------------------------------
# global variables

previous_result = ""
previous_result_n = ""



async def get_last_n_element(params : dict) -> str | None:
    async with InfluxDBClientAsync(url=influxhost, token=token, org=org) as client:
        
        location = f'from(bucket: "{bucket}")'

        range_component = f'|> range(start: -40m)'

        measurement_filter = '|> filter(fn: (r) => r._measurement == "' + f'" or r._measurement == "'.join(params['measurements']) + '")'

        aspect_filter = '|> filter(fn: (r) => r.aspect == "' + f'" or r.aspect == "'.join(params['aspects']) + '")'
        
        variable_filter = '|> filter(fn: (r) => r.variable == "' + f'" or r.variable == "'.join(params['variables']) + '")'

        drop = '|> drop(columns: ["_start", "_stop", "sensor", "_field", "host", "org", "student", "topic", "aspect", "result"])'

        count = f"|> limit(n: {params['record_count']})"

        flux_query = f'{location} {range_component} {measurement_filter} {variable_filter} {drop} {count}'

        global previous_result_n

        try:
            query_api = client.query_api()
            result = await query_api.query(org=org, query=flux_query)
            result_json = result.to_json()
            if result_json == previous_result_n:
                return None
            else:
                previous_result_n = result_json
                return result_json
        except Exception as e:
            print(f"Error querying InfluxDB: {str(e)}")
            return None
        


# get last element for each aspect
async def get_last_element(params : dict) -> str | None:
    async with InfluxDBClientAsync(url=influxhost, token=token, org=org) as client:
        
        location = f'from(bucket: "{bucket}")'

        range_component = f'|> range(start: {params["start_time"]})'

        measurement_filter = '|> filter(fn: (r) => r._measurement == "' + f'" or r._measurement == "'.join(params['measurements']) + '")'

        aspect_filter = '|> filter(fn: (r) => r.aspect == "' + f'" or r.aspect == "'.join(params['aspects']) + '")'
        
        variable_filter = '|> filter(fn: (r) => r.variable == "' + f'" or r.variable == "'.join(params['variables']) + '")'

        drop = '|> drop(columns: ["_start", "_stop", "sensor", "_field", "host", "org", "student", "topic", "aspect", "result"])'

        count = f"|> last()"

        flux_query = f'{location} {range_component} {measurement_filter} {variable_filter} {drop} {count}'

        global previous_result

        try:
            query_api = client.query_api()
            result = await query_api.query(org=org, query=flux_query)
            result_json = result.to_json()
            if result_json == previous_result:
                return None
            else:
                previous_result = result_json
                return result_json
        except Exception as e:
            print(f"Error querying InfluxDB: {str(e)}")
            return None





if __name__ == '__main__':
    # Create an event loop
    loop = asyncio.get_event_loop()

    # Call the asynchronous function using the event loop and await the result
    df = loop.run_until_complete(get_last_element(influx_query.query_home))

    # Close the event loop
    loop.close()

    print(str(type(df)))
    
    if df is not None:
        #dfAsString = json.dump(df, './querydata.json')
        # Process the DataFrame or write to a CSV file
        with open('./querydata.json', 'w') as f:
            #for list in df:
            #    dfAsString += list.to_csv()
            f.write(df)
        #f.close()
    else:
        print("qery returned Null")
    