import heapq
import time

from Train_Pathfinder.Utils import *
from Train_Pathfinder.ConnectionsMap import *


def a_star(graph, start_name, end_name, start_datetime, cost_fn, heuristic_fn):
    start_id, end_id = resolve_names(graph, start_name, end_name)

    if not start_id or not end_id:
        return None, None, None, None, None

    start_date = start_datetime.date()
    start_time = start_datetime.hour * 3600 + start_datetime.minute * 60 + start_datetime.second
    start_processing_time = time.time()

    # minimal cost, and a set of all the route names that can reach there with that cost
    # the set is needed to reconsider the station if the cost is based in any way on transfers,
    # since otherwise it can lead to early relaxation of paths passing through a closed node
    g_score = {start_id: (0, set())}

    # State: (f_score, g_score, current_date, current_time, transfers, station_id, last_trip, path)
    h_start = heuristic_fn(graph, start_id, end_id, None)
    queue = [(h_start, 0, start_date, start_time, 0, start_id, None, [])]

    while queue:
        (current_f, current_g,
         current_date, current_time, transfers, station_id, last_trip, path_until_now) = heapq.heappop(queue)

        station_g_score = g_score.get(station_id, None)
        if current_g > (float('inf') if station_g_score is None else station_g_score[0]):
            continue

        if station_id == end_id:
            calc_time = time.time() - start_processing_time
            total_time = (current_date - start_date).days * 86400 + current_time - start_time
            return path_until_now, round(current_g,0), total_time, transfers, calc_time

        for connection in graph.stations[station_id].connections:

            min_departure = current_time + (120 if last_trip and connection.trip_id != last_trip else 0)
            departure_date = current_date
            if connection.departure_time < min_departure:
                departure_date += timedelta(days=1)

            actual_date = connection.service.first_available_date(departure_date)
            if not actual_date: continue

            is_transfer = last_trip is not None and connection.trip_id != last_trip
            new_transfers = transfers + (1 if is_transfer else 0)
            g_neighbor = cost_fn(connection, start_date, actual_date, start_time, current_g, is_transfer)


            neighbor_g_score = g_score.get(connection.target_id, None)
            neighbor_g_score_value = float('inf') if neighbor_g_score is None else neighbor_g_score[0]

            if g_neighbor < neighbor_g_score_value + 1:
                if g_neighbor == neighbor_g_score_value:
                    if connection.route_name in neighbor_g_score[1]:
                        continue
                    else:
                        neighbor_g_score[1].add(connection.route_name)
                else:
                    g_score[connection.target_id] = (g_neighbor, {connection.route_name})

                h_neighbor = heuristic_fn(graph, connection.target_id, end_id, connection.route_name)

                # 3. f(n) = g(n) + h(n)
                f_neighbor = g_neighbor + h_neighbor

                new_path = path_until_now + [{
                    'from': graph.stations[station_id].name,
                    'to': graph.stations[connection.target_id].name,
                    'line': connection.route_name,
                    'dep': connection.departure_time,
                    'arr': connection.arrival_time,
                    'date': actual_date,
                }]

                heapq.heappush(queue, (
                    f_neighbor,
                    g_neighbor,
                    actual_date,
                    connection.arrival_time,
                    new_transfers,
                    connection.target_id,
                    connection.trip_id,
                    new_path
                ))

    return None, None, None, None, None

def modal_a_star(graph, start_name, end_name, start_datetime, mode):
    if mode == 't':
        return a_star(graph, start_name, end_name, start_datetime, cost_time, heuristic_time)
    elif mode == 'p':
        return a_star(graph, start_name, end_name, start_datetime, cost_transfers, heuristic_transfers)
    return None, None, None, None, None



def cost_time(conn, start_date, actual_date, start_time_secs, current_g, is_transfer):
    total_days = (actual_date - start_date).days
    return total_days * 86400 + conn.arrival_time - start_time_secs


def heuristic_time(graph, current_id, target_id, current_line):
    """Estimating time to travel to the target station in seconds,
    traveling in a straight line at 100km/h"""
    c = graph.stations[current_id]
    t = graph.stations[target_id]
    dist = haversine(c.latitude, c.longitude, t.latitude, t.longitude)
    return (dist / 100) * 3600


def cost_transfers(conn, start_date, actual_date, start_time_secs, current_g, is_transfer):

    # tiny penalty for the time taken - causes the algorithm to swap to a faster route if it has
    # the same amount of transfers
    time_cost = cost_time(conn, start_date, actual_date, start_time_secs, current_g, is_transfer) / very_large_number

    return current_g + (1 if is_transfer else 0) + time_cost

def heuristic_transfers(graph, current_id, target_id, current_line):
    """Complex heuristic for transfer based A*. Combines 2 costs:
    1. distance divided by 10^12 - used for tiebreakers when transfers are equal, should choose the route that
    goes towards the target first
    2. not a direct line penalty - applies if not currently traveling on a direct line to the target,
    which makes the algorithm instantly turn towards the target if there's a direct line to it"""
    curr_st = graph.stations[current_id]
    target_st = graph.stations[target_id]

    dist = haversine(curr_st.latitude, curr_st.longitude, target_st.latitude, target_st.longitude)

    distance_penalty = dist / large_number

    route_penalty = 0.5
    if current_line in target_st.lines:
        route_penalty = 0

    return route_penalty + distance_penalty


if __name__ == "__main__":
    start_station = "wrocław główny" #input("Stacja początkowa: ")
    end_station = "zielona góra główna" #input("Stacja końcowa: ")
    graph = FullGTFSGraph("/home/emilia/Documents/train_data")
    start_datetime = datetime.now() - timedelta(hours=1)
    res_time = a_star(graph, start_station, end_station, start_datetime, cost_time, heuristic_time)
    print_results(start_datetime, res_time)
    print()
    print()
    res_transfers = a_star(graph, start_station, end_station, start_datetime,
                           cost_transfers, heuristic_transfers)
    print_results(start_datetime, res_transfers)