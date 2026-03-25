import random
import time
import sys
from itertools import combinations
from datetime import timedelta
from Train_Pathfinder.Algorithms.A_star import modal_a_star


def calculate_full_route_cost(graph, start_name, permutation, start_datetime, mode='t'):
    """
    Helper function to calculate the total cost of a specific order of stops.
    The arrival time at one stop becomes the departure time for the next segment.
    """
    current_time = start_datetime
    total_score = 0
    total_time = 0
    total_transfers = 0
    full_path = []

    # Complete sequence: Start -> Permutation -> Start
    sequence = [start_name] + list(permutation) + [start_name]

    last_segment_route = None

    for origin, destination in zip(sequence, sequence[1:]):

        # Calculate the best path for the current segment
        seg_path, cost, seg_time, seg_transfers, _ = modal_a_star(
            graph, origin, destination, current_time, mode
        )

        if last_segment_route is not None and seg_path[0]['line'] != last_segment_route:
            seg_transfers += 1

        # If any segment is unreachable, the entire route is invalid
        if seg_path is None:
            return float('inf'), float('inf'), float('inf'), None

        full_path.extend(seg_path)

        # Increment clock for the next segment based on travel time
        current_time += timedelta(seconds=seg_time)

        total_score += cost
        total_time += seg_time
        total_transfers += seg_transfers

        last_segment_route = seg_path[-1]['line']


    return total_score, total_time, total_transfers, full_path


def tabu_search(graph, start_name, L, start_datetime,
                mode='t', iterations=20, sample_size=None):

    if sample_size is None:
        lenL = len(L)
        num_of_perms = lenL * (lenL - 1) / 2
        sample_size = num_of_perms // 2
    start_processing_time = time.time()

    # Initial state
    current_perm = list(L)
    best_perm = list(current_perm)
    best_score, best_time, best_transfers, best_path = calculate_full_route_cost(
        graph, start_name, best_perm, start_datetime, mode
    )

    # Task 2 (b): Variable Tabu list size based on the length of L
    max_tabu_size = max(1, int(len(L) * 0.7))
    tabu_list = []  # Stores 'moves' as tuple (station1, station2)

    for i in range(iterations):
        # print(f"{int(i * 100 / iterations)}%", file=sys.stderr)
        # Generate all possible swaps (Neighborhood)
        all_possible_swaps = list(combinations(range(len(current_perm)), 2))

        # Task 2 (d): Neighborhood sampling strategy to reduce computation time
        if sample_size and sample_size < len(all_possible_swaps):
            candidate_swaps = random.sample(all_possible_swaps, sample_size)
        else:
            candidate_swaps = all_possible_swaps

        best_neighbor_perm = None
        best_neighbor_score = float('inf')
        best_neighbor_time = float('inf')
        best_neighbor_transfers = float('inf')
        best_neighbor_path = None
        chosen_move = None

        for move in candidate_swaps:
            idx1, idx2 = move
            # Apply swap
            neighbor_perm = list(current_perm)
            neighbor_perm[idx1], neighbor_perm[idx2] = neighbor_perm[idx2], neighbor_perm[idx1]

            n_score, n_time, n_transfers, n_path = calculate_full_route_cost(
                graph, start_name, neighbor_perm, start_datetime, mode
            )

            station1, station2 = neighbor_perm[idx1], neighbor_perm[idx2]

            # Task 2 (c): Aspiration Criterion
            # If move is tabu but results in a new global best, we accept it
            is_tabu = (station1, station2) in tabu_list or (station2, station1) in tabu_list

            if not is_tabu or n_score < best_score:
                if n_score < best_neighbor_score:
                    best_neighbor_score = n_score
                    best_neighbor_time = n_time
                    best_neighbor_transfers = n_transfers
                    best_neighbor_path = n_path
                    best_neighbor_perm = neighbor_perm
                    chosen_move = (station1, station2)

        # If a valid neighbor was found, move to that state
        if best_neighbor_perm:
            current_perm = best_neighbor_perm

            # Update Tabu List
            tabu_list.append(chosen_move)
            if len(tabu_list) > max_tabu_size:
                tabu_list.pop(0)

            # Update Global Best
            if best_neighbor_score < best_score:
                best_score = best_neighbor_score
                best_time = best_neighbor_time
                best_transfers = best_neighbor_transfers
                best_path = best_neighbor_path

    calculation_time = time.time() - start_processing_time
    return best_path, best_score, best_time, best_transfers, calculation_time


if __name__ == "__main__":
    from Train_Pathfinder.ConnectionsMap import FullGTFSGraph
    from Train_Pathfinder.Utils import print_results
    from datetime import datetime

    # Load data
    graph = FullGTFSGraph("/home/emilia/Documents/train_data")

    # Inputs for Task 2
    A = "Wrocław Główny"
    L = ["Legnica", "Wałbrzych Główny", "Jaworzyna Śląska", "Zielona Góra Główna", "Głogów", "Lubin", "Jelenia góra"]
    start_datetime = datetime.now()
    opt_mode = 't'

    res = tabu_search(graph, A, L, start_datetime,
                      mode=opt_mode, iterations=10)

    path, score, time, transfers, calc_time = res

    print_results(start_datetime, res)