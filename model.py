from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Experiment(Base):
    __tablename__ = 'experiment'

    id = Column(Integer, primary_key=True)
    group_limit = Column(Integer, nullable=False)
    group_size_limit = Column(Integer, nullable=False)
    broadcast_frequency = Column(Integer, nullable=False)
    deliveries = relationship('Delivery', backref='experiment')
    deliveries_qry = relationship('Delivery', lazy="dynamic")

    @property
    def heard_deliveries(self):
        return self.deliveries_qry.filter(Delivery.recipient_id != None).all()

    @property
    def unheard_deliveries(self):
        return self.deliveries_qry.filter(Delivery.recipient_id == None).all()

    @property
    def decrypted_deliveries(self):
        return self.deliveries_qry.filter(Delivery.decrypted).all()

    @property
    def undecrypted_deliveries(self):
        return self.deliveries_qry.filter(not Delivery.decrypted).all()

    def __repr__(self):
        return "<Experiment id={} group_limit={} group_size_limit={} broadcast_frequency={}>".format(self.id,
                                                                                                     self.group_limit,
                                                                                                     self.group_size_limit,
                                                                                                     self.broadcast_frequency)


class Node(Base):
    __tablename__ = 'node'

    id = Column(Integer, primary_key=True)
    broadcasts = relationship('Broadcast', backref='sender')
    deliveries = relationship('Delivery', backref='recipient')

    def __repr__(self):
        return "<Node id={}>".format(self.id)


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    group_limit = Column(Integer, nullable=False, index=True)
    group_size_limit = Column(Integer, nullable=False, index=True)
    nodes = relationship('Membership', backref='group')

    def __repr__(self):
        return "<Group id={} group_limit={} group_size_limit={}>".format(self.id, self.group_limit,
                                                                         self.group_size_limit)


class Contact(Base):
    __tablename__ = 'contact'

    id = Column(Integer, primary_key=True)
    node_1 = Column(Integer, ForeignKey('node.id'), nullable=False)
    node_2 = Column(Integer, ForeignKey('node.id'), nullable=False)
    time_start = Column(Integer, nullable=False)
    time_end = Column(Integer, nullable=False)

    def __repr__(self):
        return "<Contact id={} node_1={} node_2={} time_start={} time_end={}>".format(self.id, self.node_1, self.node_2,
                                                                                      self.time_start, self.time_end)


class Broadcast(Base):
    __tablename__ = 'broadcast'

    id = Column(Integer, primary_key=True)
    frequency = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)
    sender_id = Column(Integer, ForeignKey('node.id'), nullable=False)
    deliveries = relationship('Delivery', backref='broadcast')

    def __repr__(self):
        return "<Broadcast id={} frequency={} time={} sender={} deliveries=...>".format(self.id, self.frequency,
                                                                                        self.time, self.sender)


class Delivery(Base):
    __tablename__ = 'delivery'

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey('experiment.id'), nullable=False)
    broadcast_id = Column(Integer, ForeignKey('broadcast.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('node.id'))
    decrypted = Column(Boolean)

    def __repr__(self):
        return "<Delivery id={} experiment={} broadcast={} recipient={} decrypted={}>".format(self.id, self.experiment,
                                                                                              self.broadcast,
                                                                                              self.recipient,
                                                                                              self.decrypted)


# association tables below #

class Membership(Base):
    __tablename__ = 'membership'

    node_id = Column(Integer, ForeignKey('node.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('group.id'), primary_key=True)
    node = relationship('Node', backref='membership')

# engine = create_engine('sqlite:///sqlalchemy_example.db')
engine = create_engine('postgresql://ana@/mobility')
Base.metadata.create_all(engine)
