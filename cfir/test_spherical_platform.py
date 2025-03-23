from entity import Entity
from receptor import Receptor
from horizon import Horizon
from zone import Zone
from mesh import Mesh
from universe import Universe

def test_spherical_platform():
    # Create a Universe
    universe = Universe("universe_1")

    # Create a Mesh
    mesh = Mesh("mesh_1")

    # Create Entities
    entity1 = Entity("entity_1", 10, 0.5, 1.0)
    entity2 = Entity("entity_2", 15, 1.0, 1.5)
    entity3 = Entity("entity_3", 20, 1.5, 2.0)

    # Register Entities in the Mesh
    mesh.register_entity(entity1)
    mesh.register_entity(entity2)
    mesh.register_entity(entity3)

    # Create Receptors
    receptor1 = Receptor("receptor_1", "temperature", 5, entity1)
    receptor2 = Receptor("receptor_2", "humidity", 5, entity2)
    receptor3 = Receptor("receptor_3", "temperature", 5, entity3)

    # Add Receptors to Entities
    entity1.store_data("temperature", 22.5)
    entity2.store_data("humidity", 60)
    entity3.store_data("temperature", 20)

    # Create Horizons for Entities
    horizon1 = Horizon("horizon_1", entity1)
    horizon2 = Horizon("horizon_2", entity2)
    horizon3 = Horizon("horizon_3", entity3)

    # Add Receptors to Horizons
    horizon1.add_receptor(receptor1)
    horizon2.add_receptor(receptor2)
    horizon3.add_receptor(receptor3)

    # Create a Zone and register Entities
    zone = Zone("zone_1", "Test Zone")
    zone.add_entity(entity1)
    zone.add_entity(entity2)
    zone.add_entity(entity3)

    # Register Zone in the Universe
    universe.add_zone(zone)

    # Connect Entities in the Mesh
    mesh.connect_entities(entity1.entity_id, entity2.entity_id)
    mesh.connect_entities(entity2.entity_id, entity3.entity_id)

    # Perform a global query in the Universe
    print("Global Query Results:")
    results = universe.global_query(15, 1.0, 1.5, data_type="temperature")
    print(results)

    # Visualize the Mesh
    print("\nMesh Visualization:")
    mesh.visualize_mesh()

    # Visualize the Universe
    print("\nUniverse Visualization:")
    universe.visualize_universe()

# Run the test function
if __name__ == "__main__":
    test_spherical_platform() 