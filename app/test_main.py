from fastapi.testclient import TestClient
from repository import db_models, database
from config import configs
from sqlalchemy.orm import sessionmaker
from .main import app, get_db


engine = database.get_engine(configs.SQLALCHEMY_DATABASE_URL_TESTING)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_models.Base.metadata.create_all(bind=engine)

# override the db connection to point to the test db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_net_flows():
    response = client.get("/flows/net?country_from=UK&country_to=DE&date=2021-06-06")
    assert response.status_code == 200

def test_read_directed_flows():
    response = client.get("/flows/directed?country_from=UK&country_to=DE&date=2021-06-06")
    assert response.status_code == 200

def test_unknown_flow_type_path_parameter():
    response = client.get("/flows/unknown?country_from=UK&country_to=DE&date=2021-06-06")
    assert response.status_code == 422
    assert "value is not a valid enumeration member; permitted: 'net', 'directed'" in response.text

def test_unknown_country_code_query_parameter():
    response = client.get("/flows/net?country_from=UKK&country_to=DE&date=2021-06-06")
    assert response.status_code == 422
    assert "value is not a valid enumeration member;" in response.text

def test_unknown_date_format():
    response = client.get("/flows/net?country_from=UK&country_to=DE&date=06-06-2021")
    assert response.status_code == 422
    assert "invalid date format" in response.text