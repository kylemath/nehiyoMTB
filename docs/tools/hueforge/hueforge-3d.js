/* hueforge-3d.js
 *
 * Three.js 3D preview + STL export for the HueForge designer.
 *
 * Ported from kylemath/IllumiStack (main.js) — same mesh topology
 * (top heightmap + flat bottom + four side walls), but wrapped in a
 * tidy class so the app code stays small.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export class HueForge3DPreview {
    constructor(container) {
        this.container = container;
        this.mesh = null;
        this.geometry = null;
        this.meshData = null;
        this.animating = false;
        this._initThree();
    }

    _initThree() {
        const { clientWidth, clientHeight } = this.container;
        const w = Math.max(clientWidth, 200);
        const h = Math.max(clientHeight, 200);

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x050505);

        this.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 2000);
        this.camera.position.set(0, 80, 140);

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setPixelRatio(window.devicePixelRatio || 1);
        this.renderer.setSize(w, h);
        this.container.appendChild(this.renderer.domElement);

        this.scene.add(new THREE.AmbientLight(0x666666, 1));
        const key = new THREE.DirectionalLight(0xffffff, 1.1);
        key.position.set(1, 1.4, 1);
        this.scene.add(key);
        const fill = new THREE.DirectionalLight(0xffffff, 0.45);
        fill.position.set(-1, 0.4, -0.6);
        this.scene.add(fill);

        this.scene.add(new THREE.GridHelper(200, 20, 0x222222, 0x161616));

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.08;

        const ro = new ResizeObserver(() => this.handleResize());
        ro.observe(this.container);
    }

    handleResize() {
        if (!this.renderer || !this.container) return;
        const { clientWidth, clientHeight } = this.container;
        const w = Math.max(clientWidth, 200);
        const h = Math.max(clientHeight, 200);
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    }

    startAnimation() {
        if (this.animating) return;
        this.animating = true;
        const loop = () => {
            if (!this.animating) return;
            requestAnimationFrame(loop);
            this.controls.update();
            this.renderer.render(this.scene, this.camera);
        };
        loop();
    }

    /**
     * Build a closed mesh from a heightmap and per-pixel colour buffer
     * (the *modified* image — i.e. the predicted print appearance).
     *
     * @param {Float32Array} heightMap  width*height floats in mm
     * @param {Uint8ClampedArray} colorPixels  RGBA buffer of the modified image
     * @param {number} imgWidth
     * @param {number} imgHeight
     * @param {object} opts
     * @param {number} opts.modelWidth   mm
     */
    buildMesh(heightMap, colorPixels, imgWidth, imgHeight, opts) {
        const { modelWidth } = opts;
        const aspect = imgWidth / imgHeight;
        const modelHeight = modelWidth / aspect;

        const scaleX = modelWidth / imgWidth;
        const scaleZ = modelHeight / imgHeight;

        const vertices = [];
        const colors = [];
        const indices = [];

        /* TOP surface vertices. */
        for (let y = 0; y < imgHeight; y++) {
            for (let x = 0; x < imgWidth; x++) {
                const posX = (x - imgWidth / 2) * scaleX;
                const posZ = (y - imgHeight / 2) * scaleZ;
                const posY = heightMap[y * imgWidth + x];
                vertices.push(posX, posY, posZ);

                const idx = (y * imgWidth + x) * 4;
                colors.push(
                    colorPixels[idx]     / 255,
                    colorPixels[idx + 1] / 255,
                    colorPixels[idx + 2] / 255
                );
            }
        }

        /* TOP triangles. */
        for (let y = 0; y < imgHeight - 1; y++) {
            for (let x = 0; x < imgWidth - 1; x++) {
                const a = y * imgWidth + x;
                const b = y * imgWidth + (x + 1);
                const c = (y + 1) * imgWidth + x;
                const d = (y + 1) * imgWidth + (x + 1);
                indices.push(a, b, d);
                indices.push(a, d, c);
            }
        }

        /* BOTTOM surface (flat at Y=0). */
        const bottomStart = vertices.length / 3;
        for (let y = 0; y < imgHeight; y++) {
            for (let x = 0; x < imgWidth; x++) {
                const posX = (x - imgWidth / 2) * scaleX;
                const posZ = (y - imgHeight / 2) * scaleZ;
                vertices.push(posX, 0, posZ);

                const idx = (y * imgWidth + x) * 4;
                colors.push(
                    colorPixels[idx]     / 255,
                    colorPixels[idx + 1] / 255,
                    colorPixels[idx + 2] / 255
                );
            }
        }
        for (let y = 0; y < imgHeight - 1; y++) {
            for (let x = 0; x < imgWidth - 1; x++) {
                const a = bottomStart + y * imgWidth + x;
                const b = bottomStart + y * imgWidth + (x + 1);
                const c = bottomStart + (y + 1) * imgWidth + x;
                const d = bottomStart + (y + 1) * imgWidth + (x + 1);
                indices.push(a, d, b);
                indices.push(a, c, d);
            }
        }

        /* WALLS. */
        const W = imgWidth, H = imgHeight;
        for (let x = 0; x < W - 1; x++) {
            const tl = x, tr = x + 1;
            const bl = bottomStart + x, br = bottomStart + x + 1;
            indices.push(tl, bl, br);
            indices.push(tl, br, tr);
        }
        for (let x = 0; x < W - 1; x++) {
            const tl = (H - 1) * W + x;
            const tr = (H - 1) * W + x + 1;
            const bl = bottomStart + (H - 1) * W + x;
            const br = bottomStart + (H - 1) * W + x + 1;
            indices.push(tl, tr, br);
            indices.push(tl, br, bl);
        }
        for (let y = 0; y < H - 1; y++) {
            const tf = y * W, tb = (y + 1) * W;
            const bf = bottomStart + y * W, bb = bottomStart + (y + 1) * W;
            indices.push(tf, tb, bb);
            indices.push(tf, bb, bf);
        }
        for (let y = 0; y < H - 1; y++) {
            const tf = y * W + (W - 1);
            const tb = (y + 1) * W + (W - 1);
            const bf = bottomStart + y * W + (W - 1);
            const bb = bottomStart + (y + 1) * W + (W - 1);
            indices.push(tf, bf, bb);
            indices.push(tf, bb, tb);
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
        geometry.setIndex(indices);
        geometry.computeVertexNormals();

        if (this.mesh) {
            this.scene.remove(this.mesh);
            this.geometry?.dispose();
        }

        const material = new THREE.MeshPhongMaterial({
            vertexColors: true,
            side: THREE.DoubleSide,
            shininess: 18
        });
        this.mesh = new THREE.Mesh(geometry, material);
        this.scene.add(this.mesh);
        this.geometry = geometry;

        this.meshData = {
            vertices, indices,
            width: modelWidth,
            height: modelHeight
        };

        this.startAnimation();
        return this.meshData;
    }

    /** Generate binary STL buffer for the current mesh (matches IllumiStack format). */
    exportBinarySTL(filename = 'hueforge_model.stl') {
        if (!this.meshData) {
            throw new Error('No mesh has been generated yet.');
        }

        const { vertices, indices } = this.meshData;
        const numTriangles = indices.length / 3;
        const bufferSize = 80 + 4 + (numTriangles * 50);
        const buffer = new ArrayBuffer(bufferSize);
        const view = new DataView(buffer);

        const header = 'Binary STL generated by nehiyoMTB / HueForge';
        for (let i = 0; i < Math.min(header.length, 80); i++) {
            view.setUint8(i, header.charCodeAt(i));
        }
        view.setUint32(80, numTriangles, true);

        let offset = 84;
        for (let i = 0; i < indices.length; i += 3) {
            const i1 = indices[i] * 3, i2 = indices[i + 1] * 3, i3 = indices[i + 2] * 3;
            const v1 = [vertices[i1], vertices[i1 + 1], vertices[i1 + 2]];
            const v2 = [vertices[i2], vertices[i2 + 1], vertices[i2 + 2]];
            const v3 = [vertices[i3], vertices[i3 + 1], vertices[i3 + 2]];

            const u = [v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]];
            const v = [v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]];
            const n = [
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0]
            ];
            const len = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) || 1;

            view.setFloat32(offset, n[0] / len, true); offset += 4;
            view.setFloat32(offset, n[1] / len, true); offset += 4;
            view.setFloat32(offset, n[2] / len, true); offset += 4;

            for (const v of [v1, v2, v3]) {
                view.setFloat32(offset, v[0], true); offset += 4;
                view.setFloat32(offset, v[1], true); offset += 4;
                view.setFloat32(offset, v[2], true); offset += 4;
            }
            view.setUint16(offset, 0, true); offset += 2;
        }

        const blob = new Blob([buffer], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        return { numTriangles, bytes: bufferSize };
    }
}
