class Horizon:
    def __init__(self, horizon_id, attached_entity):
        self.horizon_id = horizon_id  # Unique identifier for each Horizon instance
        self.attached_entity = attached_entity  # The Entity object to which this Horizon is attached
        self.receptors = []  # List containing all the Receptor objects attached to the Entity

    def add_receptor(self, receptor):
        """Adds a new receptor to the Horizon, updating the detection range accordingly."""
        self.receptors.append(receptor)

    def remove_receptor(self, receptor_id):
        """Removes an existing receptor by its ID."""
        self.receptors = [r for r in self.receptors if r.receptor_id != receptor_id]

    def calculate_max_detection_radius(self):
        """Calculates the maximum detection radius across all attached receptors."""
        return max(receptor.radius for receptor in self.receptors) if self.receptors else 0

    def detect_all_data(self, universe_data):
        """Aggregates and returns all data points detected by receptors within their respective detection radii."""
        all_detected_data = []
        for receptor in self.receptors:
            detected_data = receptor.detect_data(universe_data)
            all_detected_data.extend(detected_data)
        return all_detected_data 