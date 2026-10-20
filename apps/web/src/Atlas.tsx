import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { catalog, request } from './lib/api';
import type { Estimate, Manifest, Star } from './lib/api';
import { decodeMap, scenePosition } from './lib/map-format';
import type { Position, MapRecord } from './lib/map-format';
import { radiusPc } from './lib/state';
import type { View } from './lib/state';

export type CameraState = { camera: Position; target: Position };
type Props = { snapshot: string; view: View; selected?: Star; route?: Estimate; progress?: number;
  cameraRef: React.MutableRefObject<CameraState | undefined>; onPick: (ordinal: number) => void; onCount?: (count: number) => void };

export function Atlas(props: Props) {
  const host = useRef<HTMLDivElement>(null);
  const current = useRef(props); current.current = props;
  const [status, setStatus] = useState('Loading map…');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const element = host.current!;
    const controller = new AbortController();
    let renderer: THREE.WebGLRenderer;
    try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); }
    catch { setStatus('3D is unavailable. Use the searchable star list and journey controls.'); return; }
    let disposed = false;
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.domElement.setAttribute('aria-label', 'Interactive 3D star atlas. Drag to orbit, scroll to zoom. Use the list to select with a keyboard.');
    element.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, .001, 6000);
    const extent = radiusPc(props.view.radius);
    camera.position.fromArray(props.view.camera ?? [extent * 1.15, extent * .8, extent * 1.15]);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.fromArray(props.view.target ?? [0, 0, 0]);
    controls.minDistance = .05; controls.maxDistance = 1000; controls.enableDamping = false;
    if (camera.position.distanceTo(controls.target) < .001) camera.position.z += 1;
    const geometry = new THREE.BufferGeometry();
    const material = new THREE.PointsMaterial({ size: 3, sizeAttenuation: false, vertexColors: true });
    const stars = new THREE.Points(geometry, material); scene.add(stars);
    const sun = new THREE.Mesh(new THREE.SphereGeometry(.08, 12, 8), new THREE.MeshBasicMaterial({ color: '#ffca70' })); scene.add(sun);
    const selected = new THREE.Mesh(new THREE.SphereGeometry(.12, 12, 8), new THREE.MeshBasicMaterial({ color: '#58cfe5', wireframe: true })); scene.add(selected);
    const traveler = new THREE.Mesh(new THREE.SphereGeometry(.09, 10, 8), new THREE.MeshBasicMaterial({ color: '#ffffff' })); scene.add(traveler);
    const grid = new THREE.GridHelper(extent * 2, 20, '#29455b', '#15283b'); scene.add(grid);
    const rings = new THREE.Group(); scene.add(rings);
    for (const r of [10, 25, 50, 100, 200, 326.16].filter(v => v <= props.view.radius)) {
      const points = Array.from({ length: 129 }, (_, i) => new THREE.Vector3(Math.cos(i / 128 * Math.PI * 2) * radiusPc(r), 0, Math.sin(i / 128 * Math.PI * 2) * radiusPc(r)));
      rings.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color: '#35536b' })));
    }
    const routeGeometry = new THREE.BufferGeometry();
    const route = new THREE.Line(routeGeometry, new THREE.LineBasicMaterial({ color: '#58cfe5' })); scene.add(route);
    const axes = new THREE.AxesHelper(Math.max(.5, extent / 5)); scene.add(axes);
    const sunLabel = document.createElement('span'); sunLabel.className = 'map-label'; sunLabel.textContent = 'Sun'; element.appendChild(sunLabel);
    const selectionLabel = document.createElement('span'); selectionLabel.className = 'map-label'; element.appendChild(selectionLabel);
    function placeLabel(node: HTMLSpanElement, position: THREE.Vector3, visible: boolean) {
      const p = position.clone().project(camera);
      node.hidden = !visible || p.z > 1 || p.z < -1 || Math.abs(p.x) > 1 || Math.abs(p.y) > 1;
      node.style.left = `${(p.x + 1) / 2 * element.clientWidth + 8}px`;
      node.style.top = `${(-p.y + 1) / 2 * element.clientHeight}px`;
    }
    let lastObserver = props.view.camera ? props.view.observer : 'sun';
    let lastRoute = '';
    function render() {
      if (disposed) return;
      const p = current.current;
      grid.visible = p.view.plane; rings.visible = p.view.rings;
      selected.visible = !!p.selected;
      if (p.selected) selected.position.fromArray(scenePosition(p.selected.position_pc));
      if (p.view.observer !== lastObserver) {
        lastObserver = p.view.observer;
        const target = p.selected?.source_id === lastObserver ? scenePosition(p.selected.position_pc) : [0, 0, 0];
        controls.target.fromArray(target); camera.position.copy(controls.target).add(new THREE.Vector3(.5, .3, .5));
      }
      const key = p.route ? JSON.stringify([p.route.origin_position_pc, p.route.destination_position_pc]) : '';
      if (key !== lastRoute) {
        lastRoute = key;
        routeGeometry.setFromPoints(p.route ? [new THREE.Vector3(...scenePosition(p.route.origin_position_pc)), new THREE.Vector3(...scenePosition(p.route.destination_position_pc))] : []);
      }
      route.visible = !!p.route; traveler.visible = !!p.route;
      if (p.route) traveler.position.lerpVectors(new THREE.Vector3(...scenePosition(p.route.origin_position_pc)), new THREE.Vector3(...scenePosition(p.route.destination_position_pc)), p.progress ?? 0);
      controls.update();
      p.cameraRef.current = { camera: camera.position.toArray() as unknown as Position, target: controls.target.toArray() as unknown as Position };
      placeLabel(sunLabel, sun.position, p.view.labels);
      selectionLabel.textContent = p.selected?.aliases[0] ?? p.selected?.source_id ?? '';
      placeLabel(selectionLabel, selected.position, p.view.labels && !!p.selected && p.selected.source_id !== 'sun');
      renderer.render(scene, camera);
    }
    renderer.setAnimationLoop(render);
    const resize = new ResizeObserver(() => {
      renderer.setSize(element.clientWidth, element.clientHeight); camera.aspect = element.clientWidth / Math.max(element.clientHeight, 1); camera.updateProjectionMatrix();
    }); resize.observe(element);
    let records: MapRecord[] = [];
    let down = [0, 0];
    const pointerDown = (e: PointerEvent) => { down = [e.clientX, e.clientY]; };
    const pointerUp = (e: PointerEvent) => {
      if (Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
      const box = element.getBoundingClientRect();
      const ray = new THREE.Raycaster(); ray.params.Points.threshold = camera.position.distanceTo(controls.target) * .008;
      ray.setFromCamera(new THREE.Vector2((e.clientX - box.left) / box.width * 2 - 1, -(e.clientY - box.top) / box.height * 2 + 1), camera);
      const hit = ray.intersectObject(stars)[0];
      if (ray.intersectObject(sun).length) current.current.onPick(0);
      else if (hit?.index != null) current.current.onPick(records[hit.index].ordinal);
    };
    const contextLost = (event: Event) => { event.preventDefault(); setStatus('3D context lost. Use the list or retry the map.'); renderer.setAnimationLoop(null); };
    renderer.domElement.addEventListener('pointerdown', pointerDown); renderer.domElement.addEventListener('pointerup', pointerUp);
    renderer.domElement.addEventListener('webglcontextlost', contextLost);
    setStatus('Loading map…');
    async function load() {
      try {
        const manifest = await request<Manifest>(`${catalog(props.snapshot)}/map?radius_ly=${props.view.radius}`, { signal: controller.signal });
        if (disposed) return;
        current.current.onCount?.(manifest.total_count);
        let next = 0, completed = 0;
        const pieces: (readonly MapRecord[])[] = [];
        // Three concurrent fetches; complete chunks are filtered before drawing and picking.
        await Promise.all(Array.from({ length: Math.min(3, manifest.chunks.length) }, async () => {
          while (next < manifest.chunks.length) {
            const index = next++; const chunk = manifest.chunks[index];
            const response = await fetch(chunk.url, { signal: controller.signal });
            if (!response.ok) throw new Error('Map chunk unavailable.');
            const buffer = await response.arrayBuffer();
            const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', buffer)), v => v.toString(16).padStart(2, '0')).join('');
            if (buffer.byteLength !== chunk.uncompressed_bytes || digest !== chunk.uncompressed_sha256) throw new Error('Map checksum mismatch.');
            pieces[index] = decodeMap(buffer); completed++;
            if (!disposed) setStatus(`Loading map ${completed}/${manifest.chunks.length}…`);
          }
        }));
        if (disposed) return;
        // Ordinals are sorted by float64 catalog radius; count avoids float32 boundary rounding.
        records = pieces.flat().filter(r => r.ordinal <= manifest.total_count);
        const positions = new Float32Array(records.length * 3), colors = new Float32Array(records.length * 3);
        records.forEach((r, i) => {
          positions.set(scenePosition(r.positionPc), i * 3);
          const color = r.colorIndex == null ? new THREE.Color('#f0f3fa') : new THREE.Color().setHSL(.62 - THREE.MathUtils.clamp(r.colorIndex / 3, 0, 1) * .6, .65, .75);
          colors.set(color.toArray(), i * 3);
        });
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3)); geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3)); geometry.computeBoundingSphere();
        setStatus('');
      } catch (error) { if (!disposed && !controller.signal.aborted) setStatus(error instanceof Error ? error.message : 'Map unavailable.'); }
    }
    void load();
    return () => {
      disposed = true; controller.abort(); resize.disconnect(); renderer.setAnimationLoop(null); controls.dispose();
      renderer.domElement.removeEventListener('pointerdown', pointerDown); renderer.domElement.removeEventListener('pointerup', pointerUp); renderer.domElement.removeEventListener('webglcontextlost', contextLost);
      scene.traverse(object => {
        const mesh = object as THREE.Mesh;
        mesh.geometry?.dispose();
        if (mesh.material) for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) m.dispose();
      });
      renderer.dispose(); renderer.domElement.remove(); sunLabel.remove(); selectionLabel.remove();
    };
  }, [props.snapshot, props.view.radius, attempt]);
  return <div className="atlas-shell"><div className="atlas" ref={host} />
    <div className="map-caption">Galactic X → right · Z → up · Y → depth<br />Reference rings in light-years · enlarged points · J2016.0</div>
    {status && <div className="map-status" role="status">{status}<button onClick={() => setAttempt(a => a + 1)}>Retry map</button></div>}
  </div>;
}
