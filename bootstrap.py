import model
from sqlalchemy.orm import sessionmaker


def get_mobility_session(echo=False, autocommit=False):
    """returns a session to the database"""

    engine = model.create_engine('postgresql://ana@/mobility', echo=echo).execution_options(autocommit=autocommit)
    model.Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    return DBSession()