/* hueforge-app.js
 *
 * Wires the UI of index.html to the pure math in hueforge-core.js and
 * the 3D preview in hueforge-3d.js. Also defines the sign presets that
 * the user originally asked for (Farmer's Daughter, I See You, Purple
 * Haze sky gradient).
 *
 * No business logic lives in here — only DOM glue + presets.
 */

import {
    processThreshold,
    processTransmission,
    buildLayerPlan,
    buildHeightMap,
    hexToRgb
} from './hueforge-core.js';
import { HueForge3DPreview } from './hueforge-3d.js';

/* ===================================================================== */
/*  SIGN PRESETS                                                          */
/*  Each preset = an image URL + a palette + a mode + recommended layers. */
/* ===================================================================== */

const PRESETS = {
    'farmers-daughter': {
        label: "Farmer's Daughter (portrait)",
        image: '../../assets/FarmersDaughter/farmer_daughter_portrait.png',
        mode: 'threshold',
        background: '#0a0a0a',
        totalLayers: 20,
        layerHeight: 0.08,
        baseLayers: 3,
        palette: [
            { color: '#5b2a86', startLayer: 1,  mixFactor: 0.35, td: 4, label: 'Deep purple' },
            { color: '#9b6cb3', startLayer: 6,  mixFactor: 0.30, td: 5, label: 'Mid purple' },
            { color: '#e7c9a9', startLayer: 12, mixFactor: 0.30, td: 6, label: 'Sepia skin' },
            { color: '#ffffff', startLayer: 17, mixFactor: 0.50, td: 8, label: 'White highlight' }
        ]
    },
    'i-see-you': {
        label: 'I See You (kiwâpamitin)',
        image: '../../assets/kiwapamitin/iseeyousign.png',
        mode: 'threshold',
        background: '#ffffff',
        totalLayers: 15,
        layerHeight: 0.08,
        baseLayers: 3,
        palette: [
            { color: '#ffffff', startLayer: 1,  mixFactor: 0.50, td: 6, label: 'White background' },
            { color: '#202020', startLayer: 6,  mixFactor: 0.55, td: 3, label: 'Black syllabics' },
            { color: '#dc3545', startLayer: 11, mixFactor: 0.45, td: 4, label: 'Red accent' }
        ]
    },
    'purple-haze': {
        label: 'Purple Haze (full sign)',
        image: '../../assets/nipamayatan_pekiseyahk/purple_haze.png',
        mode: 'transmission',
        background: '#0a0a0a',
        totalLayers: 24,
        layerHeight: 0.08,
        baseLayers: 3,
        palette: [
            { color: '#3a1a4e', startLayer: 1,  mixFactor: 0.40, td: 3, label: 'Mountain silhouette (opaque purple)' },
            { color: '#7c4dff', startLayer: 7,  mixFactor: 0.35, td: 5, label: 'Purple haze (translucent)' },
            { color: '#c779d0', startLayer: 14, mixFactor: 0.30, td: 6, label: 'Pink sky (translucent)' },
            { color: '#ffd6e7', startLayer: 20, mixFactor: 0.30, td: 8, label: 'Soft white glow' }
        ]
    },
    'purple-haze-sky': {
        label: 'Purple Haze (sky only — pink→purple gradient)',
        image: '../../assets/nipamayatan_pekiseyahk/purple_haze.png',
        mode: 'transmission',
        background: '#1a0533',
        totalLayers: 18,
        layerHeight: 0.08,
        baseLayers: 2,
        palette: [
            { color: '#4b0d6b', startLayer: 1,  mixFactor: 0.40, td: 3,  label: 'Deep night base' },
            { color: '#7c4dff', startLayer: 5,  mixFactor: 0.30, td: 5,  label: 'Mid purple (translucent)' },
            { color: '#b86bd6', startLayer: 9,  mixFactor: 0.28, td: 6,  label: 'Magenta haze (translucent)' },
            { color: '#ffb1d8', startLayer: 13, mixFactor: 0.28, td: 7,  label: 'Pink wash (translucent)' },
            { color: '#fff2f7', startLayer: 16, mixFactor: 0.40, td: 10, label: 'White highlight' }
        ]
    }
};

/* ===================================================================== */
/*  STATE                                                                 */
/* ===================================================================== */

const state = {
    sourceImage: null,             /* HTMLImageElement that's loaded */
    sourcePixels: null,            /* Uint8ClampedArray RGBA */
    sourceWidth: 0,
    sourceHeight: 0,
    modifiedPixels: null,          /* Uint8ClampedArray RGBA */
    palette: [],                   /* Layer[] */
    backgroundColor: '#000000',
    totalLayers: 15,
    layerHeight: 0.08,
    baseLayers: 3,
    compensateFirstLayer: true,
    mode: 'threshold',             /* 'threshold' | 'transmission' */
    mixStrength: 0.3,              /* default per-layer mix factor for new colours */
    modelWidth: 100                /* mm */
};

/* ===================================================================== */
/*  DOM REFS                                                              */
/* ===================================================================== */

const $ = (id) => document.getElementById(id);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const els = {
    presetSelect: $('preset-select'),
    imageInput: $('image-input'),
    recomputeBtn: $('recompute-btn'),
    resetBtn: $('reset-btn'),
    imageInfo: $('image-info'),

    totalLayers: $('total-layers'),
    totalLayersReadout: $('total-layers-readout'),
    layerHeight: $('layer-height'),
    layerHeightReadout: $('layer-height-readout'),
    baseLayers: $('base-layers'),
    baseLayersReadout: $('base-layers-readout'),
    compensate: $('compensate-first-layer'),

    paletteList: $('palette-list'),
    addColorBtn: $('add-color-btn'),
    backgroundColor: $('background-color'),
    mixStrength: $('mix-strength'),
    mixStrengthReadout: $('mix-strength-readout'),
    mixStrengthRow: $('mix-strength-row'),

    modelWidth: $('model-width'),
    generateMeshBtn: $('generate-mesh-btn'),
    downloadStlBtn: $('download-stl-btn'),
    meshInfo: $('mesh-info'),

    originalCanvas: $('original-canvas'),
    modifiedCanvas: $('modified-canvas'),
    threeFrame: $('three-frame'),
    threePlaceholder: $('three-placeholder'),
    layerPlan: $('layer-plan')
};

let preview3D = null;

/* ===================================================================== */
/*  PALETTE RENDERING                                                     */
/* ===================================================================== */

function renderPalette() {
    els.paletteList.innerHTML = '';

    state.palette.forEach((layer, idx) => {
        const row = document.createElement('div');
        row.className = 'palette-row';

        const swatch = document.createElement('input');
        swatch.type = 'color';
        swatch.className = 'palette-swatch';
        swatch.value = layer.color;
        swatch.addEventListener('input', e => {
            layer.color = e.target.value;
            scheduleRecompute();
        });

        const meta = document.createElement('div');
        meta.className = 'palette-meta';

        const name = document.createElement('input');
        name.type = 'text';
        name.className = 'name';
        name.value = layer.label || `Colour ${idx + 1}`;
        name.placeholder = `Colour ${idx + 1}`;
        name.addEventListener('change', e => {
            layer.label = e.target.value;
            updateLayerPlan();
        });

        const startRow = document.createElement('div');
        startRow.className = 'td-row';
        const startLabel = document.createElement('span');
        startLabel.textContent = `Starts at layer ${layer.startLayer}`;
        const startSlider = document.createElement('input');
        startSlider.type = 'range';
        startSlider.className = 'threshold-slider';
        startSlider.min = 1;
        startSlider.max = state.totalLayers;
        startSlider.value = layer.startLayer;
        startSlider.addEventListener('input', e => {
            layer.startLayer = parseInt(e.target.value, 10);
            startLabel.textContent = `Starts at layer ${layer.startLayer}`;
            scheduleRecompute();
        });
        startRow.appendChild(startSlider);
        startRow.appendChild(startLabel);

        meta.appendChild(name);
        meta.appendChild(startRow);

        /* Threshold mode = per-colour mix factor.
           Transmission mode = per-colour TD (transmission distance). */
        if (state.mode === 'threshold') {
            const mixRow = document.createElement('div');
            mixRow.className = 'td-row';
            const mixSlider = document.createElement('input');
            mixSlider.type = 'range';
            mixSlider.min = 0.05; mixSlider.max = 1; mixSlider.step = 0.05;
            mixSlider.value = layer.mixFactor ?? state.mixStrength;
            const mixReadout = document.createElement('span');
            mixReadout.textContent = `mix ${(+mixSlider.value).toFixed(2)}`;
            mixSlider.addEventListener('input', e => {
                layer.mixFactor = parseFloat(e.target.value);
                mixReadout.textContent = `mix ${layer.mixFactor.toFixed(2)}`;
                scheduleRecompute();
            });
            mixRow.appendChild(mixSlider);
            mixRow.appendChild(mixReadout);
            meta.appendChild(mixRow);
        } else {
            const tdRow = document.createElement('div');
            tdRow.className = 'td-row';
            const tdSlider = document.createElement('input');
            tdSlider.type = 'range';
            tdSlider.min = 1; tdSlider.max = 20; tdSlider.step = 0.5;
            tdSlider.value = layer.td ?? 4;
            const tdReadout = document.createElement('span');
            tdReadout.textContent = `TD ${(+tdSlider.value).toFixed(1)}L`;
            tdSlider.addEventListener('input', e => {
                layer.td = parseFloat(e.target.value);
                tdReadout.textContent = `TD ${layer.td.toFixed(1)}L`;
                scheduleRecompute();
            });
            tdRow.appendChild(tdSlider);
            tdRow.appendChild(tdReadout);
            meta.appendChild(tdRow);
        }

        const move = document.createElement('div');
        move.className = 'palette-move';
        const up = document.createElement('button');
        up.textContent = '▲';
        up.title = 'Move up';
        up.addEventListener('click', () => movePaletteEntry(idx, -1));
        const down = document.createElement('button');
        down.textContent = '▼';
        down.title = 'Move down';
        down.addEventListener('click', () => movePaletteEntry(idx, +1));
        move.appendChild(up);
        move.appendChild(down);

        const del = document.createElement('button');
        del.className = 'palette-delete';
        del.textContent = '×';
        del.title = 'Remove colour';
        del.addEventListener('click', () => {
            state.palette.splice(idx, 1);
            renderPalette();
            scheduleRecompute();
        });

        row.appendChild(swatch);
        row.appendChild(meta);
        row.appendChild(move);
        row.appendChild(del);
        els.paletteList.appendChild(row);
    });
}

function movePaletteEntry(idx, dir) {
    const target = idx + dir;
    if (target < 0 || target >= state.palette.length) return;
    const [item] = state.palette.splice(idx, 1);
    state.palette.splice(target, 0, item);
    renderPalette();
    scheduleRecompute();
}

function addColor() {
    const defaults = ['#dc3545', '#7c4dff', '#ffd6e7', '#202020', '#ffffff'];
    const next = defaults[state.palette.length % defaults.length];
    const lastStart = state.palette.length
        ? state.palette[state.palette.length - 1].startLayer
        : 0;
    state.palette.push({
        color: next,
        startLayer: Math.min(state.totalLayers, lastStart + Math.max(1, Math.round(state.totalLayers / 5))),
        mixFactor: state.mixStrength,
        td: 4,
        label: ''
    });
    renderPalette();
    scheduleRecompute();
}

/* ===================================================================== */
/*  IMAGE LOADING                                                         */
/* ===================================================================== */

function loadImageFromUrl(url) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = url;
    });
}

function loadImageFromFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = e.target.result;
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

/**
 * Down-sample the source image into a working canvas so the processing
 * loops stay snappy on big photos (cap longest side at ~512px).
 */
function adoptSourceImage(img) {
    const MAX_DIM = 512;
    let w = img.naturalWidth || img.width;
    let h = img.naturalHeight || img.height;
    const scale = Math.min(1, MAX_DIM / Math.max(w, h));
    w = Math.max(1, Math.round(w * scale));
    h = Math.max(1, Math.round(h * scale));

    const work = document.createElement('canvas');
    work.width = w; work.height = h;
    const ctx = work.getContext('2d');
    ctx.drawImage(img, 0, 0, w, h);
    const data = ctx.getImageData(0, 0, w, h);

    state.sourceImage = img;
    state.sourcePixels = new Uint8ClampedArray(data.data);
    state.sourceWidth = w;
    state.sourceHeight = h;
    state.modifiedPixels = new Uint8ClampedArray(data.data.length);

    /* Draw original to its canvas. */
    drawToCanvas(els.originalCanvas, data, w, h);
    els.imageInfo.textContent = `${w}×${h} px working buffer (display only; STL uses true heightmap).`;
}

function drawToCanvas(canvas, imageData, w, h) {
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    ctx.putImageData(imageData, 0, 0);
}

/* ===================================================================== */
/*  RECOMPUTE PIPELINE                                                    */
/* ===================================================================== */

let recomputeTimer = null;
function scheduleRecompute() {
    clearTimeout(recomputeTimer);
    recomputeTimer = setTimeout(recompute, 60);
}

function recompute() {
    if (!state.sourcePixels) {
        updateLayerPlan();
        return;
    }
    /* Clamp palette starts to total. */
    state.palette.forEach(p => {
        p.startLayer = Math.max(1, Math.min(state.totalLayers, p.startLayer | 0));
    });

    const opts = {
        palette: state.palette,
        backgroundColor: state.backgroundColor,
        totalLayers: state.totalLayers
    };

    if (state.mode === 'threshold') {
        processThreshold(state.sourcePixels, state.modifiedPixels, opts);
    } else {
        processTransmission(state.sourcePixels, state.modifiedPixels, opts);
    }

    const w = state.sourceWidth, h = state.sourceHeight;
    const modData = new ImageData(state.modifiedPixels, w, h);
    drawToCanvas(els.modifiedCanvas, modData, w, h);

    updateLayerPlan();
}

/* ===================================================================== */
/*  LAYER PLAN RENDERING                                                  */
/* ===================================================================== */

function updateLayerPlan() {
    const plan = buildLayerPlan({
        palette: state.palette,
        backgroundColor: state.backgroundColor,
        totalLayers: state.totalLayers,
        layerHeight: state.layerHeight,
        baseLayers: state.baseLayers,
        compensateFirstLayer: state.compensateFirstLayer
    });

    if (plan.length === 0) {
        els.layerPlan.innerHTML = '<div class="hint">No palette configured yet.</div>';
        return;
    }

    els.layerPlan.innerHTML = '';
    plan.forEach(p => {
        const row = document.createElement('div');
        row.className = 'layer-plan-row';

        const swatch = document.createElement('span');
        swatch.className = 'layer-plan-swatch';
        swatch.style.background = p.color;

        const range = document.createElement('span');
        range.className = 'layer-plan-range';
        range.textContent = p.fromLayer === p.toLayer
            ? `Layer ${p.fromLayer}`
            : `Layers ${p.fromLayer}–${p.toLayer}`;

        const label = document.createElement('span');
        label.className = 'layer-plan-label';
        label.textContent = p.td != null
            ? `${p.label}  (TD ${p.td.toFixed(1)}L)`
            : p.label;

        const height = document.createElement('span');
        height.className = 'layer-plan-height';
        height.textContent = `${p.fromZ.toFixed(2)}–${p.toZ.toFixed(2)} mm`;

        row.appendChild(swatch);
        row.appendChild(range);
        row.appendChild(label);
        row.appendChild(height);
        els.layerPlan.appendChild(row);
    });

    const totalZ = state.baseLayers * state.layerHeight
        + state.totalLayers * state.layerHeight
        + (state.compensateFirstLayer ? state.layerHeight : 0);
    const footer = document.createElement('div');
    footer.className = 'layer-plan-footer';
    footer.textContent = `Total print height ≈ ${totalZ.toFixed(2)} mm `
        + `(${state.baseLayers} base + ${state.totalLayers} relief layers at `
        + `${state.layerHeight} mm${state.compensateFirstLayer ? ' + first-layer compensation' : ''}).`;
    els.layerPlan.appendChild(footer);
}

/* ===================================================================== */
/*  3D MESH                                                                */
/* ===================================================================== */

function generateMesh() {
    if (!state.sourcePixels) {
        alert('Load an image first.');
        return;
    }
    if (!preview3D) {
        els.threePlaceholder?.remove();
        preview3D = new HueForge3DPreview(els.threeFrame);
    }
    const heightMap = buildHeightMap(
        state.sourcePixels, state.sourceWidth, state.sourceHeight,
        {
            totalLayers: state.totalLayers,
            layerHeight: state.layerHeight,
            baseLayers: state.baseLayers,
            compensateFirstLayer: state.compensateFirstLayer
        }
    );
    const meshData = preview3D.buildMesh(
        heightMap, state.modifiedPixels,
        state.sourceWidth, state.sourceHeight,
        { modelWidth: state.modelWidth }
    );
    els.downloadStlBtn.disabled = false;
    els.meshInfo.textContent =
        `${(meshData.vertices.length / 3).toLocaleString()} vertices · `
        + `${(meshData.indices.length / 3).toLocaleString()} triangles · `
        + `${meshData.width.toFixed(1)} × ${meshData.height.toFixed(1)} mm footprint`;
}

function downloadStl() {
    if (!preview3D) {
        alert('Generate the 3D mesh first.');
        return;
    }
    const result = preview3D.exportBinarySTL();
    els.meshInfo.textContent =
        `Downloaded STL: ${result.numTriangles.toLocaleString()} triangles, `
        + `${(result.bytes / 1024 / 1024).toFixed(2)} MB`;
}

/* ===================================================================== */
/*  PRESETS                                                               */
/* ===================================================================== */

async function loadPreset(key) {
    const preset = PRESETS[key];
    if (!preset) return;

    /* Switch settings *first* so renderPalette sees the right mode. */
    state.mode = preset.mode;
    state.backgroundColor = preset.background;
    state.totalLayers = preset.totalLayers;
    state.layerHeight = preset.layerHeight;
    state.baseLayers = preset.baseLayers;
    state.palette = preset.palette.map(p => ({ ...p }));

    els.backgroundColor.value = state.backgroundColor;
    els.totalLayers.value = state.totalLayers;
    els.totalLayersReadout.textContent = state.totalLayers;
    els.layerHeight.value = state.layerHeight;
    els.layerHeightReadout.textContent = state.layerHeight.toFixed(2);
    els.baseLayers.value = state.baseLayers;
    els.baseLayersReadout.textContent = state.baseLayers;
    $$('input[name="mode"]').forEach(r => { r.checked = r.value === state.mode; });
    syncModeSpecificUI();
    renderPalette();

    try {
        const img = await loadImageFromUrl(preset.image);
        adoptSourceImage(img);
        recompute();
    } catch (e) {
        console.warn('Preset image failed to load:', e);
        els.imageInfo.textContent =
            `Could not load preset image (${preset.image}). Upload one manually.`;
    }
}

function syncModeSpecificUI() {
    /* The "default mix factor" slider only meaningfully applies to threshold
       mode, but keep it visible so the user can adjust the *initial* mix
       used when they add a new colour in either mode. */
    els.mixStrengthRow.style.opacity = state.mode === 'threshold' ? '1' : '0.5';
}

/* ===================================================================== */
/*  INIT                                                                  */
/* ===================================================================== */

function init() {
    /* Default palette: a simple 3-colour stack to demonstrate. */
    state.palette = [
        { color: '#000000', startLayer: 1,  mixFactor: 0.5, td: 3, label: 'Black' },
        { color: '#dc3545', startLayer: 6,  mixFactor: 0.4, td: 5, label: 'Red' },
        { color: '#ffffff', startLayer: 11, mixFactor: 0.5, td: 8, label: 'White' }
    ];

    /* Populate preset dropdown labels from PRESETS (they were also
       hard-coded in HTML; this just keeps them in sync). */
    Object.entries(PRESETS).forEach(([key, preset]) => {
        const opt = els.presetSelect.querySelector(`option[value="${key}"]`);
        if (opt) opt.textContent = preset.label;
    });

    /* Listeners. */
    els.presetSelect.addEventListener('change', e => {
        if (e.target.value) loadPreset(e.target.value);
    });
    els.imageInput.addEventListener('change', async e => {
        const file = e.target.files?.[0];
        if (!file) return;
        try {
            const img = await loadImageFromFile(file);
            adoptSourceImage(img);
            recompute();
        } catch (err) {
            console.error(err);
            alert('Failed to load image.');
        }
    });
    els.recomputeBtn.addEventListener('click', () => recompute());
    els.resetBtn.addEventListener('click', () => {
        if (state.sourcePixels && state.modifiedPixels) {
            state.modifiedPixels.set(state.sourcePixels);
            const data = new ImageData(state.modifiedPixels, state.sourceWidth, state.sourceHeight);
            drawToCanvas(els.modifiedCanvas, data, state.sourceWidth, state.sourceHeight);
        }
    });

    bindRange(els.totalLayers, els.totalLayersReadout, v => {
        state.totalLayers = parseInt(v, 10);
        state.palette.forEach(p => {
            p.startLayer = Math.min(state.totalLayers, p.startLayer);
        });
        renderPalette();
        scheduleRecompute();
    });
    bindRange(els.layerHeight, els.layerHeightReadout, v => {
        state.layerHeight = parseFloat(v);
        scheduleRecompute();
    }, 2);
    bindRange(els.baseLayers, els.baseLayersReadout, v => {
        state.baseLayers = parseInt(v, 10);
        scheduleRecompute();
    });
    bindRange(els.mixStrength, els.mixStrengthReadout, v => {
        state.mixStrength = parseFloat(v);
    }, 2);

    els.compensate.addEventListener('change', e => {
        state.compensateFirstLayer = e.target.checked;
        scheduleRecompute();
    });
    els.backgroundColor.addEventListener('input', e => {
        state.backgroundColor = e.target.value;
        scheduleRecompute();
    });
    els.addColorBtn.addEventListener('click', addColor);

    $$('input[name="mode"]').forEach(r => {
        r.addEventListener('change', e => {
            state.mode = e.target.value;
            syncModeSpecificUI();
            renderPalette();
            scheduleRecompute();
        });
    });

    els.modelWidth.addEventListener('change', e => {
        const v = parseFloat(e.target.value);
        if (Number.isFinite(v) && v > 0) state.modelWidth = v;
    });
    els.generateMeshBtn.addEventListener('click', generateMesh);
    els.downloadStlBtn.addEventListener('click', downloadStl);

    syncModeSpecificUI();
    renderPalette();
    updateLayerPlan();
}

function bindRange(input, readout, fn, decimals = 0) {
    const update = () => {
        const v = input.value;
        readout.textContent = decimals === 0
            ? String(parseInt(v, 10))
            : parseFloat(v).toFixed(decimals);
        fn(v);
    };
    input.addEventListener('input', update);
}

document.addEventListener('DOMContentLoaded', init);
