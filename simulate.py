import logging
import matplotlib.pyplot as plt
import statistics
import pylab
import psycopg2
import random
from multiprocessing import Pool

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_
from model import *
import yaml


def run(args):
    database, time_limit, experiment_id = args
    # start a database session:
    engine = create_engine(database, echo=False).execution_options(autocommit=False)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # fetch the parameters:
    experiment = session.query(Experiment).filter(Experiment.id == experiment_id).one()
    group_limit = experiment.group_limit
    group_size_limit = experiment.group_size_limit
    broadcast_frequency = experiment.broadcast_frequency
    print("starting experiment {}: {}-{}-{}".format(experiment_id, group_limit, group_size_limit, broadcast_frequency))
    # keep a dict of group membership count:
    groups = dict()
    matching_groups = session.query(Group). \
        filter(Group.group_limit == group_limit). \
        filter(Group.group_size_limit == group_size_limit).all()
    for group in matching_groups:
        for member in group.nodes:
            node = member.node
            groups.setdefault(node.id, [])
            groups[node.id].append(group.id)
    # keep track of next group key to use:
    next_key_index = dict()
    for node in groups:
        next_key_index[node] = random.randint(0, len(groups[node]) - 1)
    # run simulation:
    t = 0
    while t < time_limit:
        broadcasts = session.query(Broadcast).filter(Broadcast.frequency == broadcast_frequency,
                                                     Broadcast.time == t).all()
        for broadcast in broadcasts:
            sender_id = broadcast.sender_id
            # find recipients in range:
            results = session.query(Contact). \
                filter(or_(Contact.node_1 == sender_id, Contact.node_2 == sender_id)). \
                filter(Contact.time_start < t, Contact.time_end > t).all()
            recipients = []
            for contact in results:
                if contact.node_1 == sender_id:
                    recipients.append(contact.node_2)
                else:
                    recipients.append(contact.node_1)
            if len(recipients) == 0 or sender_id not in groups:
                new_delivery = Delivery(experiment=experiment, broadcast=broadcast)
            else:
                # fetch key to encrypt this round:
                key_index = next_key_index[sender_id]
                group_key = groups[node][key_index]
                #update key index:
                membership_count = len(groups[node])
                next_key_index[sender_id] = (key_index + 1) % membership_count
                # check if recipients are in the same group:
                for recipient in recipients:
                    if recipient in groups and group_key in groups[recipient]:
                        decrypted = True
                    else:
                        decrypted = False
                    new_delivery = Delivery(experiment=experiment, broadcast=broadcast, recipient_id=recipient,
                                            decrypted=decrypted)
            session.add(new_delivery)
            session.commit()
        t += 1
    print("finished {}".format(experiment_id))
    print(experiment_id, group_limit, group_size_limit, broadcast_frequency)


if __name__ == '__main__':
    database = 'postgresql://ana@/mobility'

    engine = create_engine(database, echo=False).execution_options(autocommit=False)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    with open("config.yaml", "r") as config_file:
        yaml_data = config_file.read()

    data_dict = yaml.load(yaml_data)
    group_limits = data_dict["group_limits"]
    group_sizes = data_dict["group_sizes"]
    broadcast_freqs = data_dict["broadcast_freqs"]
    node_count = data_dict["node_count"]
    total_time = data_dict["total_time"]

    config = []
    for broadcast_frequency in broadcast_freqs:
        # add baseline config:
        new_experiment = Experiment(broadcast_frequency=broadcast_frequency, group_limit=1, group_size_limit=node_count)
        session.add(new_experiment)
        session.commit()
        config.append([database, total_time, new_experiment.id])
        # add remaining configs:
        for group_limit in group_limits:
            for group_size_limit in group_sizes:
                new_experiment = Experiment(broadcast_frequency=broadcast_frequency,
                                            group_limit=group_limit,
                                            group_size_limit=group_size_limit)
                session.add(new_experiment)
                session.commit()
                config.append([database, total_time, new_experiment.id])

            # import pdb
            # pdb.set_trace()

    p = Pool(7, maxtasksperchild=1)
    p.map(run, config)
