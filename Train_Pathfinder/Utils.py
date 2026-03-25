import sys
from datetime import timedelta

transfer_time = 120

large_number = 10**4
very_large_number = 10**12

def condense_path(raw_path):
    """Condenses the path from individual connections to a transfer plan"""
    if not raw_path:
        return []
    condensed = []
    current_line = raw_path[0]['line']
    start_station = raw_path[0]['from']
    start_time = raw_path[0]['dep']
    last_station = raw_path[0]['to']
    last_arr_time = raw_path[0]['arr']
    start_date = raw_path[0]['date']

    for i in range(1, len(raw_path)):
        step = raw_path[i]
        if step['line'] != current_line:
            condensed.append((
                current_line,
                start_station,
                start_date,
                timedelta(seconds=start_time),
                last_station,
                timedelta(seconds=last_arr_time)
            ))
            current_line = step['line']
            start_station = step['from']
            start_time = step['dep']

        last_station = step['to']
        last_arr_time = step['arr']


    condensed.append((
        current_line,
        start_station,
        start_date,
        timedelta(seconds=start_time),
        last_station,
        timedelta(seconds=last_arr_time),
    ))

    return condensed



def print_results(start_time, results):
    """Prints the results of the pathfinder"""
    path, cost, time, transfers, calc_time = results
    path = condense_path(path)
    if time is None:
        print("No path found.")
        return
    print(f"Shortest path found after {timedelta(seconds=calc_time)},"
          f" takes {timedelta(seconds=time)} with {transfers} transfer{'' if transfers == 1 else 's'}.")
    print("Route:")
    current_date = start_time.date()
    for trip in path:
        line, start_station, start_date, start_time, end_station, end_time = trip
        if start_date > current_date:
            print(f"\tWait for {(start_date - current_date).days} days")
        print(f"\t{line} from {start_station} ({start_time}) to {end_station} ({end_time})")
        current_date = start_date
        if start_time > end_time:
            current_date += timedelta(days=1)
    print(f"Cost: {cost}, Calculation time: {timedelta(seconds=calc_time)}", file=sys.stderr)

import math


def haversine(latitude1, longitude1, latitude2, longitude2):
    R = 6371.0

    angle_phi1, angle_phi2 = math.radians(latitude1), math.radians(latitude2)
    angle_phi = math.radians(latitude2 - latitude1)
    angle_lambda = math.radians(longitude2 - longitude1)
    a = math.sin(angle_phi / 2) ** 2 + \
        math.cos(angle_phi1) * math.cos(angle_phi2) * \
        math.sin(angle_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def resolve_names(graph, start_name, end_name):
    start_id = None
    end_id = None
    for s_id, station in graph.stations.items():
        name_lower = station.name.strip().lower()
        if name_lower == start_name.strip().lower(): start_id = s_id
        if name_lower == end_name.strip().lower(): end_id = s_id
        if start_id and end_id: break
    return start_id, end_id