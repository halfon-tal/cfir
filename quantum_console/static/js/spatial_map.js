// Using Three.js for 3D visualization
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

class SpatialMap {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(
            75, 
            window.innerWidth / window.innerHeight, 
            0.1, 
            1000
        );
        
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        
        this.init();
    }
    
    init() {
        // Setup renderer
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.container.appendChild(this.renderer.domElement);
        
        // Setup camera
        this.camera.position.z = 5;
        
        // Add lights
        const ambientLight = new THREE.AmbientLight(0x404040);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        this.scene.add(ambientLight);
        this.scene.add(directionalLight);
        
        // Start animation loop
        this.animate();
    }
    
    updateEntities(entities) {
        // Clear existing entities
        this.clearEntities();
        
        // Add new entities
        entities.forEach(entity => {
            const mesh = this.createEntityMesh(entity);
            this.scene.add(mesh);
        });
    }
    
    createEntityMesh(entity) {
        const geometry = new THREE.SphereGeometry(0.1, 32, 32);
        const material = new THREE.MeshPhongMaterial({
            color: this.getEntityColor(entity.status)
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(
            entity.coordinates.x,
            entity.coordinates.y,
            entity.coordinates.z
        );
        
        return mesh;
    }
    
    getEntityColor(status) {
        const colors = {
            active: 0x00ff00,
            idle: 0xffff00,
            alert: 0xff0000
        };
        return colors[status] || 0x808080;
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
    
    clearEntities() {
        this.scene.children = this.scene.children.filter(
            child => child.type !== 'Mesh'
        );
    }
}

// Initialize map when document is ready
document.addEventListener('DOMContentLoaded', () => {
    const map = new SpatialMap('spatial-map');
    
    // Setup WebSocket for real-time updates
    const socket = new WebSocket('ws://' + window.location.host + '/ws');
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'entity_update') {
            map.updateEntities(data.entities);
        }
    };
}); 