import sqlalchemy as db

# connect  to postgresql with username and passwo
db_user = "example"
db_password = "example"
db_address = "db.balancechecker.orb.local"  # orbstack default address
engine = db.create_engine(
    f"postgresql://{db_user}:{db_password}@{db_address}:5432/example"
)
connection = engine.connect()
metadata = db.MetaData()

balance = db.Table("balance", metadata, autoload=True, autoload_with=engine)
user = db.Table("user", metadata, autoload=True, autoload_with=engine)
