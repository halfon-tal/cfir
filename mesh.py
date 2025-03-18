class Mesh:
    def __init__(self, mesh_id):
        self.mesh_id = mesh_id  # Unique identifier for the Mesh instance
        self.connections = {}  # Dictionary representing connections between Entities and Zones
        self.entities = {}  # Dictionary storing all Entities managed by the Mesh
        self.zones = {}  # Dictionary storing all Zones managed by the Mesh

    def register_entity(self, entity):
        """Adds an Entity into the Mesh network."""
        self.entities[entity.entity_id] = entity
        self.connections[entity.entity_id] = set()  # Initialize connections for the new entity

    def register_zone(self, zone):
        """Adds a Zone and indexes its Entities into the Mesh network."""
        self.zones[zone.zone_id] = zone
        for entity in zone.entities:
            self.register_entity(entity)

    def connect_entities(self, entity_id_1, entity_id_2):
        """Creates a direct logical connection between two entities for efficient data sharing."""
        if entity_id_1 in self.connections and entity_id_2 in self.connections:
            self.connections[entity_id_1].add(entity_id_2)
            self.connections[entity_id_2].add(entity_id_1)  # Ensure bidirectional connection

    def disconnect_entity(self, entity_id):
        """Removes all connections associated with a specified Entity."""
        if entity_id in self.connections:
            for connected_entity in list(self.connections[entity_id]):
                self.connections[connected_entity].remove(entity_id)
            del self.connections[entity_id]

    def find_path(self, entity_id_from, entity_id_to):
        """Finds the shortest interconnection path between two Entities within the Mesh."""
        from collections import deque

        if entity_id_from not in self.connections or entity_id_to not in self.connections:
            return None  # One of the entities does not exist in the mesh

        queue = deque([(entity_id_from, [entity_id_from])])
        visited = set()

        while queue:
            current_entity, path = queue.popleft()
            if current_entity == entity_id_to:
                return path  # Return the path if the destination is reached

            visited.add(current_entity)
            for neighbor in self.connections[current_entity]:
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None  # No path found

    def broadcast_data(self, entity_id, data_type, data_payload):
        """Efficiently disseminates data from a specified Entity to other connected Entities."""
        if entity_id in self.connections:
            for connected_entity in self.connections[entity_id]:
                # Assuming each entity has a method to receive data
                self.entities[connected_entity].receive_data(data_type, data_payload)

    def visualize_mesh(self):
        """Provides a graphical representation of the network structure (Zones, Entities, and their connections)."""
        print(f"Mesh ID: {self.mesh_id}")
        for entity_id, connected_entities in self.connections.items():
            print(f"Entity ID: {entity_id} is connected to: {', '.join(map(str, connected_entities))}") 