import csv
from datetime import datetime, timedelta
from functools import lru_cache


class Station:
    """Graph nodes - store references to connection objects to describe graph edges"""
    def __init__(self, stop_id, name, lat, lon):
        self.id = stop_id
        self.name = name
        self.latitude = float(lat)
        self.longitude = float(lon)
        self.connections = []
        self.lines = set()

    def __repr__(self):
        return f"Station({self.name})"

class Service:
    """Service is an object describing the conditions under which a connection is available -
    start and end date, days of the week and exceptions for holiays and stuff"""
    def __init__(self, row):
        self.service_id = row['service_id']
        self.days = {
            0: row['monday'] == '1',
            1: row['tuesday'] == '1',
            2: row['wednesday'] == '1',
            3: row['thursday'] == '1',
            4: row['friday'] == '1',
            5: row['saturday'] == '1',
            6: row['sunday'] == '1'
        }
        self.start_date = datetime.strptime(row['start_date'], '%Y%m%d').date()
        self.end_date = datetime.strptime(row['end_date'], '%Y%m%d').date()
        self.exceptions = {} # date -> exception_type (1: add, 2. remove)

    @lru_cache
    def is_active(self, date):
        """Describes if a given date fits the service criteria"""
        if date in self.exceptions:
            return self.exceptions[date] == 1
        if self.start_date <= date <= self.end_date:
            return self.days[date.weekday()]
        return False

    @lru_cache
    def first_available_date(self, start_search_date):
        """Finds the first date from the one given that fits the service criteria, or in other words,
            finds the first date from the one given that the connection will be available on"""
        current_date = start_search_date
        while current_date <= self.end_date:
            if self.is_active(current_date):
                return current_date
            current_date += timedelta(days=1)
        return None

class Connection:
    """Graph edge - describes a trip at a particular time
    with a particular service conditions (specified by a service object)"""
    def __init__(self, target_id, departure_time, arrival_time, route_name, trip_id, service):
        self.target_id = target_id
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.route_name = route_name
        self.trip_id = trip_id
        self.service = service

    def is_active_on_date(self, date):
        """Calls the service is_active_on_date method to find whether the """
        return self.service.is_active(date)


    def first_available_date(self, date):
        """Calls the service first_available_date method to find """
        return self.service.first_available_date(date)

def parse_time(t):
    """helper, writes time as seconds"""
    h, m, s = map(int, t.strip().split(':'))
    return h * 3600 + m * 60 + s


class FullGTFSGraph:
    def __init__(self, directory):
        self.directory = directory
        self.stations = {}  # Nodes - id to object dict
        self.stop_to_master = {} # Nodes - dict maps sub-stations to the parent
        self.services = {}  # Service objects - id to objct dict

        self._load_all_data()

    def _load_all_data(self):
        connection_number = 0

        # calendar.txt - service object creation, without exceptions yet
        with open(f"{self.directory}/calendar.txt", 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                self.services[row['service_id']] = Service(row)

        # calendar_dates.txt - populates services with exceptions
        with open(f"{self.directory}/calendar_dates.txt", 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                s_id = row['service_id']
                if s_id in self.services:
                    date_val = datetime.strptime(row['date'], '%Y%m%d').date()
                    self.services[s_id].exceptions[date_val] = int(row['exception_type'])

        # stops.txt - creates graph nodes (only parent stations)
        with open(f"{self.directory}/stops.txt", 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                sid, parent = row['stop_id'], row['parent_station']
                m_id = parent if parent else sid
                self.stop_to_master[sid] = m_id
                if m_id not in self.stations:
                    self.stations[m_id] = Station(m_id, row['stop_name'], row['stop_lat'], row['stop_lon'])

        # routes.txt - builds map of route ids to names for future reference
        routes = {}
        with open(f"{self.directory}/routes.txt", 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                routes[r['route_id']] = r['route_short_name'] or r['route_long_name']

        # trips.txt - maps trip id to its service id route and service
        trip_map = {}
        with open(f"{self.directory}/trips.txt", 'r', encoding='utf-8') as f:
            for t in csv.DictReader(f):
                service_obj = self.services.get(t['service_id'])
                if service_obj:
                    trip_map[t['trip_id']] = (routes[t['route_id']], service_obj)

        # stop_times.txt - edges
        with open(f"{self.directory}/stop_times.txt", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            current_trip, prev_m_id, prev_dep = None, None, None

            for row in reader:
                tid = row['trip_id']
                if tid not in trip_map: continue

                m_id = self.stop_to_master[row['stop_id']]
                route_name, service_obj = trip_map[tid]

                if tid != current_trip:
                    current_trip, prev_m_id, prev_dep = tid, m_id, parse_time(row['departure_time'])
                    continue

                arr_time = parse_time(row['arrival_time'])

                #Adding connecton, and adding the routes to the set in the target
                new_conn = Connection(m_id, prev_dep, arr_time, route_name, tid, service_obj)
                connection_number += 1
                self.stations[prev_m_id].connections.append(new_conn)
                self.stations[prev_m_id].lines.add(route_name)
                self.stations[m_id].lines.add(route_name)

                prev_m_id, prev_dep = m_id, parse_time(row['departure_time'])

        print(f"Graph built. Found {len(self.stations)} stations with {connection_number} connections")




if __name__ == "__main__":
    path = "/home/emilia/Documents/train_data"
    FullGTFSGraph(path)