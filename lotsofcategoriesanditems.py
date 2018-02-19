from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Category, Item

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()



category1 = Category(name="Soccer")
session.add(category1)
session.commit()

socceritem1 = Item(cat_id="1", title="Soccer Cleats", description="The shoes")
session.add(socceritem1)
session.commit()

socceritem1 = Item(cat_id="1", title="Jersey", description="The shirt")
session.add(socceritem1)
session.commit()


category2 = Category(name="Basketball")
session.add(category2)
session.commit()

category3 = Category(name="Baseball")
session.add(category3)
session.commit()

category4 = Category(name="Frisbee")
session.add(category4)
session.commit()

category5 = Category(name="Snowboarding")
session.add(category5)
session.commit()

snowboarditem1 = Item(cat_id="5", title="Snowboard", description="Best for any terrain and conditions.")
session.add(snowboarditem1)
session.commit()

category6 = Category(name="Rock Climbing")
session.add(category6)
session.commit()

category7 = Category(name="Foosball")
session.add(category7)
session.commit()

category8 = Category(name="Skating")
session.add(category8)
session.commit()

category9 = Category(name="Hockey")
session.add(category9)
session.commit()

print "added items!"