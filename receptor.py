from numpy import cos, sin


class Receptor:
    def __init__(self, receptor_id, data_type, radius, attached_entity):
        self.receptor_id = receptor_id  # Unique identifier for each receptor instance
        self.data_type = data_type  # Defines the kind of data it can detect
        self.radius = radius  # Detection radius around the Entity
        self.attached_entity = attached_entity  # Reference to the Entity object

    def detect_data(self, universe_data):
        """Filters and returns data points that match the receptor's data_type and fall within the detection radius."""
        detected_data = []
        entity_radius, entity_theta, entity_phi = self.attached_entity.coordinates
        
        for data_point in universe_data:
            data_radius, data_theta, data_phi, data_type = data_point
            
            # Calculate the distance between the receptor and the data point
            distance = self.calculate_distance(entity_radius, entity_theta, entity_phi, data_radius, data_theta, data_phi)
            
            if data_type == self.data_type and distance <= self.radius:
                detected_data.append(data_point)
        
        return detected_data

    def calculate_distance(self, r1, theta1, phi1, r2, theta2, phi2):
        """Calculates the distance between two points in spherical coordinates."""
        # Convert spherical to Cartesian coordinates
        x1 = r1 * sin(theta1) * cos(phi1)
        y1 = r1 * sin(theta1) * sin(phi1)
        z1 = r1 * cos(theta1)

        x2 = r2 * sin(theta2) * cos(phi2)
        y2 = r2 * sin(theta2) * sin(phi2)
        z2 = r2 * cos(theta2)

        # Calculate Euclidean distance
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2) ** 0.5 