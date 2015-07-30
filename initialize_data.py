from random import sample, choice

import networkx as nx
from numpy import random as nprandom
from sqlalchemy.orm import sessionmaker
from model import *
import yaml

from bootstrap import get_mobility_session


def parse_mobility_data(session, mobility_data_file):
    G = nx.Graph()
    with open(mobility_data_file) as mobility_data:
        nodes = dict()
        count = 0
        for line in mobility_data:
            line = line[:-1].split(" ")
            x, y = [int(s) for s in line[:2]]
            if x not in nodes:
                new_node = Node()
                session.add(new_node)
                session.commit()
                nodes[x] = new_node
                G.add_node(new_node.id)
            if y not in nodes:
                new_node = Node()
                session.add(new_node)
                session.commit()
                nodes[y] = new_node
                G.add_node(new_node.id)
            intervals = line[2:]
            for interval in intervals:
                t1, t2 = [int(float(t)) for t in interval.split("*")]
                new_contact = Contact(node_1=nodes[x].id, node_2=nodes[y].id, time_start=t1, time_end=t2)
                session.add(new_contact)
                session.commit()
            G.add_edge(nodes[x].id, nodes[y].id)
    session.commit()
    return G


def create_baseline_group(session, node_count):
    nodes = session.query(Node).all()
    new_group = Group(group_limit=1, group_size_limit=node_count)
    session.add(new_group)
    session.commit()
    for node in nodes:
        membership = Membership(group_id=new_group.id, node_id=node.id)
        session.add(membership)
        session.commit()


def create_group(session, graph, group_limit, group_size_limit):
    nodes = dict()
    while (len(graph) > 1):
        node = choice(graph.nodes())
        node_reached_group_limit = False
        long_cliques = [c for c in nx.cliques_containing_node(graph, nodes=[node])[node] if len(c) > 1]
        if len(long_cliques) == 0:
            graph.remove_node(node)
            continue
        cliques = sorted(long_cliques, key=lambda x: len(x), reverse=True)
        for clique in cliques:
            if len(clique) < 2:
                break
            l = min(len(clique), group_size_limit)
            clique.remove(node)
            group = sample(clique, l - 1) + [node]
            available = True
            for n in group:
                nodes.setdefault(n, 0)
                if nodes[n] == group_limit:
                    available = False
                    break
            if available:
                new_group = Group(group_limit=group_limit, group_size_limit=group_size_limit)
                session.add(new_group)
                session.commit()
                for n in group:
                    membership = Membership(group_id=new_group.id, node_id=n)
                    session.add(membership)
                    session.commit()
                    nodes[n] += 1
                    if nodes[n] == group_limit:
                        graph.remove_node(n)
                        if n == node:
                            node_reached_group_limit = True
            if node_reached_group_limit:
                break
    return


def generate_broadcasts(session, broadcast_frequency, total_time):
    nodes = session.query(Node).all()
    for node in nodes:
        t = nprandom.randint(0, broadcast_frequency)
        while t <= total_time - broadcast_frequency:
            new_broadcast = Broadcast(frequency=broadcast_frequency, time=t, sender_id=node.id)
            session.add(new_broadcast)
            session.commit()
            t += broadcast_frequency


if __name__ == '__main__':
    session = get_mobility_session()

    mobility_data_file = "input/nokia_trimmed.linkdump"
    graph = parse_mobility_data(session, mobility_data_file)

    with open("config.yaml", "r") as config_file:
        yaml_data = config_file.read()

    data_dict = yaml.load(yaml_data)
    group_limits = data_dict["group_limits"]
    group_sizes = data_dict["group_sizes"]
    broadcast_freqs = data_dict["broadcast_freqs"]
    node_count = data_dict["node_count"]
    total_time = data_dict["total_time"]

    #create_baseline_group(session)
    create_baseline_group(session, node_count)

    for group_limit in group_limits:
        for group_size_limit in group_sizes:
            create_group(session, graph.copy(), group_limit, group_size_limit)

    for broadcast_frequency in broadcast_freqs:
        generate_broadcasts(session, broadcast_frequency, total_time)
