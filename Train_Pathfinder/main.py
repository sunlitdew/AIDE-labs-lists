from Algorithms.Dijkstra import *
from Algorithms.Tabu_search import *

graph = FullGTFSGraph("../train_data")
start_station = "wrocław główny"
end_station = "zielona góra główna"
start_datetime = datetime.now()

L = ["Legnica", "Wałbrzych Główny", "Jaworzyna Śląska", "Lubin"]

print_results(start_datetime, dijkstra_time(graph, start_station, end_station, start_datetime))
print("------------------------------")

print_results(start_datetime, modal_a_star(graph, start_station, end_station, start_datetime, 't'))
print("------------------------------")

print_results(start_datetime, modal_a_star(graph, start_station, end_station, start_datetime, 'p'))
print("------------------------------")

print_results(start_datetime, tabu_search(graph, start_station, L, start_datetime, 't', iterations=20, sample_size=3))
