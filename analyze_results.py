#!/usr/bin/env python3

import math
import multiprocessing
import json

from bootstrap import get_mobility_session

import model


def stats_heard(heard_deliveries):
    """Returns a list with the number of broadcasts sent by each node which were heard by at least one recipient."""
    result = dict()
    for delivery in heard_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, set())
        result[sender].add(broadcast.id)
    return [len(r) for r in result.values()]


def stats_heard_with_repetition(heard_deliveries):
    """Returns a list with the number of deliveries of broadcasts sent by each node."""
    result = dict()
    for delivery in heard_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, 0)
        result[sender] += 1
    return list(result.values())


def stats_unheard(unheard_deliveries):
    """Returns a list with the number of broadcasts sent by each node which were not heard by any recipient."""
    result = dict()
    for delivery in unheard_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, 0)
        result[sender] += 1
    return list(result.values())


def stats_decrypted(decrypted_deliveries):
    """Returns a list with the number of broadcasts sent by each node which were decrypted by at least one recipient."""
    result = dict()
    for delivery in decrypted_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, set())
        result[sender].add(broadcast.id)
    return [len(r) for r in result.values()]


def stats_decrypted_with_repetition(decrypted_deliveries):
    """Returns a list with the number of deliveries of broadcasts sent by each node which were decrypted."""
    result = dict()
    for delivery in decrypted_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, 0)
        result[sender] += 1
    return list(result.values())


def stats_undecrypted(decrypted_deliveries, undecrypted_deliveries):
    """Returns a list with the number of broadcasts sent by each node which were heard but not decrypted by any
    recipient."""
    result = dict()
    for delivery in undecrypted_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, set())
        result[sender].add(broadcast.id)

    for delivery in decrypted_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, set())
        if broadcast.id in result[sender]:
            result[sender].remove(broadcast.id)
    return [len(r) for r in result.values()]


def stats_hourly_at_least_once_decrypted(decrypted_deliveries):
    """Returns a dictionary mapping a node to a list of the hourly count of frames sent by it that were decrypted
     at least once."""
    result = dict()
    for delivery in decrypted_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, 48 * [set()])
        t = math.floor(broadcast.time / 3600)  # convert to previous hour
        result[sender][t].add(broadcast.id)
    return {sender: len(result[sender]) for sender in result}


def stats_hourly_total_decrypted(decrypted_deliveries):
    """Returns a dictionary mapping a node to a list of the hourly count of frames received by it that were
    decrypted."""
    result = dict()
    for delivery in decrypted_deliveries:
        broadcast = delivery.broadcast
        sender = broadcast.sender_id
        result.setdefault(sender, 48 * [0])
        t = math.floor(broadcast.time / 3600)  # convert to previous hour
        result[sender][t] += 1
    return result


def produce_results(experiment_id):
    _session = get_mobility_session()
    experiment = _session.query(model.Experiment).get(experiment_id)

    """returns a nested dict containing params and results for one specific experiment"""
    print("{}: working on {}".format(experiment.id, experiment))
    print("{}: gathering delivery information".format(experiment.id))

    heard_deliveries = experiment.heard_deliveries
    unheard_deliveries = experiment.unheard_deliveries
    decrypted_deliveries = experiment.decrypted_deliveries
    undecrypted_deliveries = experiment.undecrypted_deliveries

    print("{}: calculating stats".format(experiment.id))

    out = dict(
        params=dict(
            group_limit=experiment.group_limit,
            group_size_limit=experiment.group_size_limit,
            broadcast_frequency=experiment.broadcast_frequency
        ),
        statistics=dict(
            heard=stats_heard(heard_deliveries),
            heard_repeated=stats_heard_with_repetition(heard_deliveries),
            unheard=stats_unheard(unheard_deliveries),
            decrypted=stats_decrypted(decrypted_deliveries),
            decrypted_repeated=stats_decrypted_with_repetition(decrypted_deliveries),
            undecrypted=stats_undecrypted(decrypted_deliveries, undecrypted_deliveries),
            hourly_once=stats_hourly_at_least_once_decrypted(decrypted_deliveries),
            hourly_total=stats_hourly_total_decrypted(decrypted_deliveries)
        )
    )

    print("{}: writing json", experiment.id)

    with open('data/statistics_{}.json'.format(experiment.id), 'w') as f:
        json.dump(out, f)

    print("{}:finished".format(experiment.id))

    session.close()


if __name__ == '__main__':
    session = get_mobility_session()

    pool = multiprocessing.Pool()

    results = pool.map(produce_results, session.query(model.Experiment.id).distinct())

