from horizon import Horizon


class Universe:
    def __init__(self, universe_id):
        self.universe_id = universe_id  # Unique identifier for the Universe instance
        self.zones = {}  # Dictionary containing all Zones, keyed by their IDs
        self.entities = {}  # Dictionary containing all Entities, keyed by their IDs
        self.spatial_index = {}  # Optional indexing structure for spatial queries

    def add_zone(self, zone):
        """Adds a Zone object to the Universe, indexing its Entities."""
        self.zones[zone.zone_id] = zone
        for entity in zone.entities:
            self.register_entity(entity, zone.zone_id)

    def remove_zone(self, zone_id):
        """Removes a Zone and its associated Entities from the Universe."""
        if zone_id in self.zones:
            zone = self.zones.pop(zone_id)
            for entity in zone.entities:
                self.remove_entity(entity.entity_id)

    def register_entity(self, entity, zone_id):
        """Registers an Entity within a specified Zone."""
        self.entities[entity.entity_id] = entity
        entity.horizon = Horizon(f"horizon_{entity.entity_id}", entity)  # Assuming each entity has a Horizon

    def remove_entity(self, entity_id):
        """Removes an Entity from the Universe and updates indexes accordingly."""
        if entity_id in self.entities:
            entity = self.entities.pop(entity_id)
            # Remove from spatial index if implemented
            # self.update_spatial_index(entity_id, remove=True)

    def global_query(self, radius, theta, phi, data_type=None):
        """Performs a global query, retrieving all data points matching criteria within a spherical area."""
        results = []
        for entity in self.entities.values():
            detected_data = entity.horizon.detect_all_data(self.get_universe_data())
            if data_type:
                detected_data = [d for d in detected_data if d[3] == data_type]  # Assuming data point has type as the fourth element
            results.extend(detected_data)
        return results

    def update_entity_position(self, entity_id, new_coordinates):
        """Updates the spatial position of an Entity and updates its references within the spatial index."""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            entity.update_coordinates(*new_coordinates)  # Assuming update_coordinates method exists

    def visualize_universe(self):
        """Provides a representation of the overall Universe structure, Zones, and Entities."""
        print(f"Universe ID: {self.universe_id}")
        for zone in self.zones.values():
            zone.visualize_zone()
        for entity in self.entities.values():
            print(f"Entity ID: {entity.entity_id}, Coordinates: {entity.coordinates}")

    def get_universe_data(self):
        """Placeholder for method to retrieve all data points in the Universe."""
        # This should return a list of data points in the format expected by detect_all_data
        return [] 