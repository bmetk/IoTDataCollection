import asyncio
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from config import influxhost, token, org, bucket

from influx_query import query_download
       

async def get_last_n_element(start_time: str) -> str | None:
    async with InfluxDBClientAsync(url=influxhost, token=token, org=org) as client:
        
        location = f'from(bucket: "{bucket}")'

        # Assembling the range component
        range_component = f'|> range(start: -40m)'

        # Assembling the measurement filter component
        measurement_filter = '|> filter(fn: (r) => r._measurement == "' + f'" or r._measurement == "'.join(query_download['measurements']) + '")'

        # Assembling the aspect filter component
        aspect_filter = '|> filter(fn: (r) => r.aspect == "' + f'" or r.aspect == "'.join(query_download['aspects']) + '")'
        
        # Assembling the variable filter component
        variable_filter = '|> filter(fn: (r) => r.variable == "' + f'" or r.variable == "'.join(query_download['variables']) + '")'

        # Filtering the columns
        drop = '|> drop(columns: ["_start", "_stop", "_field", "host"])'

        flux_query = f'{location} {range_component} {measurement_filter} {variable_filter} {drop}'

        try:
            query_api = client.query_api()
            result = await query_api.query(org=org, query=flux_query)
            result_json = result.to_json()
            return result_json
        except Exception as e:
            print(f"Error querying InfluxDB: {str(e)}")
            return None
        
