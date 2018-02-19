from sqlalchemy import Column,Integer,String,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine



Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String)
    items = relationship("Item", backref="category")

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
           'items' : [item.serialize for item in self.items],
       }

class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key = True)
    cat_id = Column(Integer, ForeignKey('category.id'))
    title = Column(String)
    description = Column(String)

    @property  
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'cat_id'         : self.cat_id,
           'description'    : self.description,
           'id'             : self.id,
           'title'          : self.title,
       }


engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)