import heapq
import time
from Train_Pathfinder.ConnectionsMap import *
from Train_Pathfinder.Utils import *


def dijkstra_time(graph, start_name, end_name, start_datetime):
    start_id = None
    end_id = None

    # find IDs from station names
    for s_id, station in graph.stations.items():
        if station.name.strip().lower() == start_name.strip().lower():
            start_id = s_id
            if end_id:
                break
        if station.name.strip().lower() == end_name.strip().lower():
            end_id = s_id
            if start_id:
                break

    if not (start_id and end_id):
        return None, None, None, None, None

    start_date = start_datetime.date()
    start_time = start_datetime.time()
    start_time_secs = 3600 * start_time.hour + 60 * start_time.minute + start_time.second

    start_processing_time = time.time()

    # State queue:
    # State variables: (elapsed seconds, current date, current time, station id, last trip id, path
    queue = [(0, start_date, start_time_secs, 0, start_id, None, [])]

    # dict of minimum time to get to each station
    min_cost = {start_id: 0}

    while queue:
        elapsed_seconds, current_date, current_time, transfers, station_id, last_trip, current_path = heapq.heappop(queue)

        # skip if longer than the shortest path
        if elapsed_seconds > min_cost.get(station_id, float('inf')):
            continue

        # destination reached
        if station_id == end_id:
            calculation_time = time.time() - start_processing_time
            return current_path, elapsed_seconds, elapsed_seconds, transfers, calculation_time

        for connection in graph.stations[station_id].connections:

            # adding cost for transfers
            min_dep_needed = current_time
            new_transfers = transfers

            if last_trip and connection.trip_id != last_trip:
                min_dep_needed += transfer_time
                new_transfers += 1

            departure_date = current_date

            # if it already left today, wait until tomorrow
            if connection.departure_time < min_dep_needed:
                departure_date += timedelta(days=1)

            # find closest departure from now
            departure_date = connection.service.first_available_date(departure_date)
            if not departure_date:
                continue

            total_days = (departure_date - start_date).days

            choice_cost = total_days * 86400 + connection.arrival_time - start_time_secs

            if choice_cost < min_cost.get(connection.target_id, float('inf')):
                min_cost[connection.target_id] = choice_cost

                new_path = current_path + [{
                    'from': graph.stations[station_id].name,
                    'to': graph.stations[connection.target_id].name,
                    'line': connection.route_name,
                    'dep': connection.departure_time,
                    'arr': connection.arrival_time,
                    'date': departure_date
                }]

                heapq.heappush(queue,
                    (choice_cost, departure_date,
                    connection.arrival_time, new_transfers, connection.target_id,
                    connection.trip_id, new_path))

    return None, None, None, None, None

if __name__ == "__main__":
    start_station = "wrocław główny" #input("Stacja początkowa: ")
    end_station = "legnica" #input("Stacja końcowa: ")
    start_datetime = datetime.now()
    res = dijkstra_time(FullGTFSGraph("/home/emilia/Documents/train_data"), start_station, end_station, start_datetime)
    print_results(start_datetime, res)
