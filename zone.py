class Zone:
    def __init__(self, zone_id, region_name):
        self.zone_id = zone_id  # Unique identifier for each Zone
        self.entities = []  # List containing references to all Entities associated with the Zone
        self.region_name = region_name  # Human-readable identifier for the Zone

    def add_entity(self, entity):
        """Adds an Entity to the Zone, incorporating its Horizon for data aggregation."""
        self.entities.append(entity)

    def remove_entity(self, entity_id):
        """Removes an Entity from the Zone by its unique ID."""
        self.entities = [e for e in self.entities if e.entity_id != entity_id]

    def query_zone_data(self, universe_data, data_type=None):
        """Queries data from the entire Zone by aggregating data from all Entities' Horizons."""
        aggregated_data = []
        for entity in self.entities:
            horizon = entity.horizon  # Assuming each entity has a Horizon attribute
            detected_data = horizon.detect_all_data(universe_data)
            if data_type:
                detected_data = [d for d in detected_data if d[3] == data_type]  # Assuming data point has type as the fourth element
            aggregated_data.extend(detected_data)
        return aggregated_data

    def aggregate_data_summary(self, universe_data, data_type):
        """Provides aggregated summary statistics for specific data types within the Zone."""
        data_points = self.query_zone_data(universe_data, data_type)
        if not data_points:
            return None
        
        values = [d[2] for d in data_points]  # Assuming the data point has a value as the third element
        return {
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'count': len(values)
        }

    def visualize_zone(self):
        """Provides a simplified visual representation of Entities and their spatial coverage within the Zone."""
        # This could be a placeholder for actual visualization logic
        print(f"Zone: {self.region_name} (ID: {self.zone_id})")
        for entity in self.entities:
            print(f" - Entity ID: {entity.entity_id}, Coordinates: {entity.coordinates}") 