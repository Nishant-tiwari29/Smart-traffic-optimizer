from services.graph import Edge, Graph, Node


def create_demo_graph() -> Graph:
    graph = Graph()
    coords = {
        "A": ("Central Station", 37.7760, -122.4170),
        "B": ("Market Street", 37.7800, -122.4130),
        "C": ("Civic Center", 37.7730, -122.4100),
        "D": ("Union Square", 37.7870, -122.4090),
        "E": ("Mission District", 37.7660, -122.4140),
        "F": ("Waterfront", 37.7930, -122.4020),
        "G": ("Embarcadero", 37.7800, -122.3970),
        "H": ("North Point", 37.7990, -122.4050),
    }
    for node_id, (name, lat, lon) in coords.items():
        graph.add_node(Node(node_id, name, lat, lon))

    road_rows = [
        ("AB", "A", "B", 1.8, 35, .78, "fair", .25),
        ("AC", "A", "C", 1.5, 30, .18, "good", .05),
        ("AE", "A", "E", 1.7, 40, .25, "good", .05),
        ("BC", "B", "C", 1.4, 30, .30, "fair", .20),
        ("BD", "B", "D", 1.2, 25, .86, "poor", .55),
        ("BF", "B", "F", 2.0, 45, .16, "good", .05),
        ("CD", "C", "D", 2.2, 40, .20, "good", .05),
        ("CE", "C", "E", 1.1, 25, .35, "fair", .25),
        ("DE", "D", "E", 2.6, 40, .72, "fair", .20),
        ("DF", "D", "F", 1.3, 35, .12, "good", .05),
        ("DG", "D", "G", 2.0, 45, .22, "good", .05),
        ("FG", "F", "G", 1.5, 30, .90, "poor", .65),
        ("FH", "F", "H", 1.4, 40, .15, "good", .05),
        ("GH", "G", "H", 2.1, 45, .24, "good", .05),
        ("EH", "E", "H", 4.8, 50, .10, "good", .05),
        ("CH", "C", "H", 5.1, 50, .48, "fair", .20),
    ]
    for road in road_rows:
        graph.add_edge(Edge(road[0], road[1], road[2], road[3], road[4], road[5], road[6], road[7]))
    return graph
