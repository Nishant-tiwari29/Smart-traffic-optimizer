from __future__ import annotations

import os

from services.graph import Graph


class DatabaseError(RuntimeError):
    pass


class MySQLStore:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "connection_timeout": 5,
        }

    @classmethod
    def from_environment(cls) -> MySQLStore | None:
        host = os.getenv("MYSQL_HOST")
        if not host:
            return None
        required = {
            "MYSQL_USER": os.getenv("MYSQL_USER"),
            "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
            "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE"),
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise DatabaseError(f"MySQL is configured incompletely; missing {', '.join(missing)}.")
        try:
            port = int(os.getenv("MYSQL_PORT", "3306"))
        except ValueError as exc:
            raise DatabaseError("MYSQL_PORT must be an integer.") from exc
        if not 1 <= port <= 65535:
            raise DatabaseError("MYSQL_PORT must be within 1..65535.")
        return cls(host, port, required["MYSQL_USER"], required["MYSQL_PASSWORD"], required["MYSQL_DATABASE"])

    def _connect(self):
        connector = self._connector()
        try:
            return connector.connect(**self.config)
        except connector.Error as exc:
            raise DatabaseError("Could not connect to the configured MySQL database.") from exc

    @staticmethod
    def _connector():
        try:
            import mysql.connector
        except ImportError as exc:
            raise DatabaseError("MySQL persistence is enabled but mysql-connector-python is not installed.") from exc
        return mysql.connector

    def load_traffic(self, graph: Graph) -> None:
        connector = self._connector()
        connection = self._connect()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT r.code, t.congestion FROM traffic_data t "
                "JOIN roads r ON r.id = t.road_id "
                "JOIN (SELECT road_id, MAX(id) AS latest_id FROM traffic_data GROUP BY road_id) latest "
                "ON latest.latest_id = t.id"
            )
            for row in cursor.fetchall():
                if row["code"] in graph.edges:
                    graph.edges[row["code"]].congestion = float(row["congestion"])
            cursor.close()
        except connector.Error as exc:
            connection.rollback()
            raise DatabaseError("Could not load current traffic from MySQL; verify schema.sql is applied.") from exc
        finally:
            connection.close()

    def save_traffic(self, road_id: str, congestion: float) -> None:
        connector = self._connector()
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO traffic_data (road_id, congestion) "
                "SELECT id, %s FROM roads WHERE code = %s",
                (congestion, road_id),
            )
            if cursor.rowcount != 1:
                raise DatabaseError(f"Road {road_id} is missing from the MySQL roads table.")
            connection.commit()
            cursor.close()
        except connector.Error as exc:
            connection.rollback()
            raise DatabaseError("Could not persist traffic update to MySQL.") from exc
        finally:
            connection.close()

    @staticmethod
    def _insert_route(cursor, result: dict) -> None:
        route = result["optimized"]
        cursor.execute(
            "INSERT INTO routes "
            "(source_intersection_id, destination_intersection_id, algorithm, distance_km, travel_time_min, optimization_cost) "
            "SELECT src.id, dst.id, 'A*', %s, %s, %s "
            "FROM intersections src "
            "JOIN locations src_loc ON src_loc.id = src.location_id AND src_loc.code = %s "
            "JOIN intersections dst ON 1=1 "
            "JOIN locations dst_loc ON dst_loc.id = dst.location_id AND dst_loc.code = %s",
            (route["distance_km"], route["travel_time_min"], route["cost"], result["source"], result["destination"]),
        )
        if cursor.rowcount != 1:
            raise DatabaseError("Route endpoints are missing from the MySQL intersections table.")
        route_id = cursor.lastrowid
        for sequence, road_code in enumerate(route["roads"]):
            cursor.execute(
                "INSERT INTO route_history (route_id, sequence_number, road_id) "
                "SELECT %s, %s, id FROM roads WHERE code = %s",
                (route_id, sequence, road_code),
            )
            if cursor.rowcount != 1:
                raise DatabaseError(f"Road {road_code} is missing from the MySQL roads table.")

    def save_route(self, result: dict) -> None:
        connector = self._connector()
        connection = self._connect()
        try:
            cursor = connection.cursor()
            self._insert_route(cursor, result)
            connection.commit()
            cursor.close()
        except connector.Error as exc:
            connection.rollback()
            raise DatabaseError("Could not persist optimized route to MySQL.") from exc
        finally:
            connection.close()

    def save_simulation(self, road_id: str, congestion: float, result: dict) -> None:
        connector = self._connector()
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO traffic_data (road_id, congestion) "
                "SELECT id, %s FROM roads WHERE code = %s",
                (congestion, road_id),
            )
            if cursor.rowcount != 1:
                raise DatabaseError(f"Road {road_id} is missing from the MySQL roads table.")
            self._insert_route(cursor, result)
            connection.commit()
            cursor.close()
        except connector.Error as exc:
            connection.rollback()
            raise DatabaseError("Could not persist simulation to MySQL.") from exc
        finally:
            connection.close()

    def route_history(self, limit: int = 50) -> list[dict]:
        connector = self._connector()
        connection = self._connect()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT r.id, src.code AS source, dst.code AS destination, r.distance_km, "
                "r.travel_time_min, r.optimization_cost "
                "FROM routes r "
                "JOIN intersections si ON si.id = r.source_intersection_id "
                "JOIN locations src ON src.id = si.location_id "
                "JOIN intersections di ON di.id = r.destination_intersection_id "
                "JOIN locations dst ON dst.id = di.location_id "
                "ORDER BY r.created_at DESC LIMIT %s",
                (limit,),
            )
            routes = cursor.fetchall()
            output = []
            for row in routes:
                cursor.execute(
                    "SELECT start_loc.code AS start_code, end_loc.code AS end_code "
                    "FROM route_history rh JOIN roads road ON road.id = rh.road_id "
                    "JOIN intersections si ON si.id = road.start_intersection_id "
                    "JOIN locations start_loc ON start_loc.id = si.location_id "
                    "JOIN intersections ei ON ei.id = road.end_intersection_id "
                    "JOIN locations end_loc ON end_loc.id = ei.location_id "
                    "WHERE rh.route_id = %s ORDER BY rh.sequence_number",
                    (row["id"],),
                )
                nodes = [row["source"]]
                for road in cursor.fetchall():
                    nodes.append(road["end_code"] if nodes[-1] == road["start_code"] else road["start_code"])
                output.append({
                    "source": row["source"],
                    "destination": row["destination"],
                    "optimized": {
                        "nodes": nodes,
                        "distance_km": float(row["distance_km"]),
                        "travel_time_min": float(row["travel_time_min"]),
                        "cost": float(row["optimization_cost"]),
                    },
                    "alternatives": [],
                })
            cursor.close()
            return output
        except connector.Error as exc:
            raise DatabaseError("Could not load route history from MySQL.") from exc
        finally:
            connection.close()

    def verify_and_load(self, graph: Graph) -> None:
        self.load_traffic(graph)
