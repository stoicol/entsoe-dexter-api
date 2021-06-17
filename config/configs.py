# static data taken from here: https://transparency.entsoe.eu/transmission-domain/physicalFlow/show
countries = {
    'NL': ['BE', 'DK', 'DE', 'NO', 'UK'],
    'DE': ['AT', 'BE', 'DK', 'FR', 'LU', 'NL', 'NO', 'PL', 'SE', 'CH']
}

# number of days to backfill the database at service startup
backfill_days = 5

SQLALCHEMY_DATABASE_URL = "sqlite:///./flows.db"
SQLALCHEMY_DATABASE_URL_TESTING = "sqlite:////tmp/flows.db"

