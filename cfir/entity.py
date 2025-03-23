class Entity:
    def __init__(self, entity_id, radius, theta, phi):
        self.entity_id = entity_id  # Unique identifier for each Entity
        self.coordinates = (radius, theta, phi)  # Spherical coordinates (r, θ, ϕ)
        self.data_storage = {}  # Embedded Sphere Database using a dictionary

    def store_data(self, data_type, data_point):
        """Store data points in the embedded database."""
        if data_type not in self.data_storage:
            self.data_storage[data_type] = []
        self.data_storage[data_type].append(data_point)

    def retrieve_data(self, radius_filter=None, data_type=None):
        """Retrieve data based on query parameters."""
        if data_type and data_type in self.data_storage:
            return self.data_storage[data_type]
        return self.data_storage

    def delete_data(self, data_type, data_point):
        """Delete a specific data point from the storage."""
        if data_type in self.data_storage:
            self.data_storage[data_type].remove(data_point)

    def update_data(self, data_type, old_data_point, new_data_point):
        """Update a specific data point in the storage."""
        if data_type in self.data_storage:
            index = self.data_storage[data_type].index(old_data_point)
            self.data_storage[data_type][index] = new_data_point

    def update_coordinates(self, radius, theta, phi):
        """Update the Entity's coordinates dynamically."""
        self.coordinates = (radius, theta, phi) 