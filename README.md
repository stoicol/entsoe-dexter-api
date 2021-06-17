# entsoe-dexter-api

This app collects and serves cross-border energy flows.

The app queries the Entso-e-API for the flows:
- it uses the [entsoe-py library](https://github.com/EnergieID/entsoe-py)
- the api-key for the Entso-e-API must be passed via environment at runtime 
- the official `Transparency Platform restful API user guide` can be found [here](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- the datapoints can be checked against the official website [here](https://transparency.entsoe.eu/transmission-domain/physicalFlow/show)
  - use the `Border - Country` tab

Application Data Model
----------------------

The data model description can be found [here](docs/DataModel.md).


Running the app locally
-----------------------

```
$ pipenv install
$ export SOURCE_API_KEY=<your api key for entsoe api>    
$ pipenv run uvicorn app.main:app
```

Once the app is running:
- the openapi specification can be found at: http://127.0.0.1:8000/docs
- point your browser at http://127.0.0.1:8000/static/dashboard.html to see chart

API Specification
-----------------

#### base URL: http://127.0.0.1:8000/

#### GET endpoint `/flows`

###### path parameter: 

`flow_type`
- required: yes 
- allowed values: net, directed

###### query parameters:

`country_from`
- required: yes
- allowed values: NL, DE, BE, UK, NO, DK, AT, FR, LU, PL, SE, CH

`country_to`
- required: yes 
- allowed values: NL, DE, BE, UK, NO, DK, AT, FR, LU, PL, SE, CH

`date`
- required: yes 
- valid format: yyyy-mm-dd


Testing
-------

#### Unit tests:

The API app tests are written using pytest and the built in FastAPI test client. 

To run all unit tests:
```
$ export SOURCE_API_KEY=<your api key for entsoe api>  
$ pipenv run pytest
```

#### Performance tests:

We can use the [vegeta](https://github.com/tsenart/vegeta) command line tool.

An example request:

`$ echo "GET http://127.0.0.1:8000/flows/net?country_code1=DE&country_code2=NL&date=2021-06-06" | vegeta attack -rate=10 -duration=10s | vegeta report`

Example report:

```
Requests      [total, rate, throughput]         100, 10.10, 10.10
Duration      [total, attack, wait]             9.906s, 9.901s, 5.139ms
Latencies     [min, mean, 50, 90, 95, 99, max]  3.237ms, 6.627ms, 6.206ms, 8.894ms, 9.898ms, 18.68ms, 26.349ms
Bytes In      [total, mean]                     3700, 37.00
Bytes Out     [total, mean]                     0, 0.00
Success       [ratio]                           100.00%
Status Codes  [code:count]                      200:100
```

Warning: Since it runs on localhost, too high load could crash the other processes.

Considerations
--------------
### database: 

Implementation uses SQLLite: single file on filesystem.

### Logging & Monitoring

Simple logging implementation to stdout (uvicorn comes with built-in logging as well).

Logs are not collected, metrics are not collected or pushed.

### Authentication

No authentication currently implemented for the API requests.

Credentials for accessing the entsoe-api are passed via environment variable at runtime. 

