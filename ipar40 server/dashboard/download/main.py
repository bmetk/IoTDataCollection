from flask import Flask, request, jsonify, Response
import pandas as pd
from influx import get_last_n_element
import asyncio

app = Flask(__name__)

async def get_data(data_range_days):
    return await get_last_n_element(data_range_days)

# API endpoint for exporting data to CSV
@app.route('/export-csv', methods=['GET'])
def export_data_to_csv():
    data_range_days = request.args.get('data_range_days')
    csv_string = ""
    try:
        #data_range_days = int(data_range_days)
        #loop = asyncio.get_event_loop()
        df = asyncio.run(get_data(data_range_days))
        if df is not None:
            df = pd.read_json(df)
            csv_string = df.to_csv(index=False, encoding="utf-8")
    except ValueError:
        csv_string = None
    
    # Return the CSV as a downloadable file
    return Response(
        csv_string,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=influxdb_data.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)