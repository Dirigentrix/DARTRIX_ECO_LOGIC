import React, { useEffect, useState } from "react";
import * as THREE from "three";

// Simple day/night theme manager with WebGL firefly effect
const ThemeManager: React.FC = () => {
  const [isNight, setIsNight] = useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Toggle theme based on system preference or manual switch
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => setIsNight(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  // Initialise minimal WebGL firefly canvas
  useEffect(() => {
    if (!containerRef.current) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    containerRef.current.appendChild(renderer.domElement);

    // Simple firefly particles (limit for mobile <15 MB RAM)
    const particles = new THREE.BufferGeometry();
    const count = 150; // keep low for performance
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 1] = Math.random() * 5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    particles.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({ color: 0xffff88, size: 0.05 });
    const pointCloud = new THREE.Points(particles, material);
    scene.add(pointCloud);

    camera.position.z = 5;
    const clock = new THREE.Clock();
    const animate = () => {
      const delta = clock.getDelta();
      // subtle floating animation
      pointCloud.rotation.y += delta * 0.1;
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    };
    animate();

    return () => {
      renderer.dispose();
      if (containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "200px",
        background: isNight ? "#001b33" : "#e0f7ff",
        transition: "background 0.5s",
      }}
    >
      {/* Firefly canvas will be inserted here */}
    </div>
  );
};

export default ThemeManager;