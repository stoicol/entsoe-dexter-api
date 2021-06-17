
## architecture

Relational database implementation, using SQLAlchemy and SQLLite.

## tables

#### data_loads
* id: int autoincremented (PK)
* country_pair_id: string
* date: date
* flows: relation to the flows table via PK-FK

This table represents a log of all the successful data loads.

Each time a data load is performed, for each `date` and `country_pair` combination, a new entry is created, which generates a new `load_id`.

Given 2 country codes, the `country_pair_id` is determined by lexicographically sorting the 2 codes.

Example: for NL and DE, the country_pair_id is DE-NL.

This means that the data is stored only for the direction dictated by the lexicographic sort.
(eg. From DE to NL)

If the user requests values corresponding to the opposite direction (eg. NL to DE), then logic is applied upon serving the response that addresses this (see [reads](##reads) section) 

#### flows
* id: int autoincremented (PK)
* load_id: string (KF to data_loads.id)
* hour: int
* flow: float
* direction: Enum(direct, opposite)

This table represents the data store of all the country flows.

Given a `load_id`, all the flows corresponding to that load_id are inserted.

The flows are retrieved and stored in UTC timezone, for all country-pair combinations.

## writes

Data is writen based on scheduled jobs that query the entsoe-api.

Job steps - for a given country_pair_id:
- get the latest date for which a load was successful
- get the latest hour for which a load was successful
- query the entsoe-api for the most recent 1.direct and 2.opposite flows between the 2 countries
- if _both_ queries are sucessful:
  - update the `data_loads`.join(`flows`) tables

### functional assumptions wrt the entsoe-py api:
- given the same _datetime_from_ and _datetime_to_ parameters, both queries (direct flows and opposite flows) to entsoe-api return same date-hour keys
- entsoe-api queries do not contain gap hours
- entsoe-api responses are deterministic: given the same query parameters, the same flow values are returned for the same date-hour pairs.

## reads

Data is read based on API GET requests.

Served data is not cached. Each new request translates into a database call.

The client can request flows for a date and 2 distinct country codes.

The client specifies the direction of the result: `country_from -> country_to`

Internally, the flows are stored based on the lexicographic sorted pair_id.

The logic related to converting the internal direction to the requested direction is performed by the router.

#### Example request net flows:
- country_from = NL
- country_to = DE

We have:
- internal direction = DE-NL
- requested direction = NL-DE

Then, the net flows as stored in the database, are `multiplied by -1`

#### Example request directed flows:
- country_from = NL
- country_to = DE

We have:
- internal direction = DE-NL
- requested direction = NL-DE

Then, the database query will return flows for `direction = opposite`

## data duplication
The data model accepts the flows for the same date and hour to be uploaded by multiple load jobs.

The query will retrieve the _latest uploaded_ flow value for a given combination of country_pair, date and hour.

This allows the job scheduler to be less precise in determining the date-hour intervals.
Since the same date-hour flow can be written by multiple load jobs, the read operations will retrieve the _latest_ uploaded flow value for each date-hour combination.

Since we assume no gap hours in the responses of the entsoe-api, violation of this assumption can lead to serving data from different load jobs in the same response (each date-hour flow is the latest loaded)

## data retention

Currently, there is no data retention implemented. 

This means that as the app runs indefinitely, the size of the database can become arbitrarily large.



