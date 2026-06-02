/* hueforge-core.js
 *
 * Pure math / image-processing for the HueForge gradient designer.
 *
 * Ported from kylemath/IllumiStack (main.js) and reworked so it
 *   - runs as a vanilla ES module (no p5.js)
 *   - works on a plain ImageData buffer
 *   - supports the original "threshold transitions" mode (IllumiStack)
 *   - and adds a "transmission stacking" mode that simulates translucent
 *     filament using each layer's transmission distance (TD), closer to
 *     the real HueForge per-layer-light-transport model.
 *
 * All functions are pure — they take input data + a config and return new
 * pixel data + a layer plan. Nothing here touches the DOM.
 */

/* ===================================================================== */
/*  COLOR UTILITIES                                                       */
/* ===================================================================== */

export function hexToRgb(hex) {
    const m = /^#?([0-9a-f]{6})$/i.exec(String(hex).trim());
    if (!m) return [0, 0, 0];
    const n = parseInt(m[1], 16);
    return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff];
}

export function rgbToHex(r, g, b) {
    const c = v => Math.max(0, Math.min(255, Math.round(v)));
    return '#' + ((1 << 24) | (c(r) << 16) | (c(g) << 8) | c(b)).toString(16).slice(1);
}

/**
 * Pigment-accurate mix between two RGB triples.
 * Uses Scrtwpns' mixbox (loaded as a global script tag) when available;
 * falls back to plain linear-RGB lerp otherwise.
 *
 *   t = 0  → returns a   (no mixing)
 *   t = 1  → returns b   (fully replaced by b)
 */
export function pigmentLerp(a, b, t) {
    if (typeof window !== 'undefined' && window.mixbox && window.mixbox.lerp) {
        const out = window.mixbox.lerp(a, b, t);
        return [out[0], out[1], out[2]];
    }
    return [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t
    ];
}

/* ===================================================================== */
/*  THRESHOLD-TRANSITIONS MODE  (the original IllumiStack behaviour)      */
/* ===================================================================== */

/**
 * @typedef {Object} ThresholdLayer
 * @property {string} color       hex
 * @property {number} startLayer  1-indexed layer where this colour first appears
 * @property {number} mixFactor   per-layer mix strength (0..1)
 * @property {string} [label]     optional human label
 */

/**
 * Process an image into the predicted print appearance using
 * the IllumiStack threshold/mixbox model.
 *
 *   For each pixel:
 *     - take its grayscale brightness (0..255)
 *     - for layer L from 1..totalLayers
 *         threshold = (255 / totalLayers) * (L - 1)
 *         if brightness >= threshold:
 *             find the palette entry whose startLayer is the latest <= L
 *             mix pixel toward that colour by mixFactor (using mixbox)
 *
 * @param {Uint8ClampedArray} srcPixels   source RGBA buffer (read-only)
 * @param {Uint8ClampedArray} dstPixels   destination RGBA buffer (will be filled)
 * @param {Object} opts
 * @param {ThresholdLayer[]} opts.palette  colours + thresholds (sorted by startLayer asc)
 * @param {string} opts.backgroundColor    "deepest" colour pixels start from
 * @param {number} opts.totalLayers
 */
export function processThreshold(srcPixels, dstPixels, opts) {
    const { palette, backgroundColor, totalLayers } = opts;
    const range = 255;
    const subd = range / totalLayers;
    const bgRgb = hexToRgb(backgroundColor);

    const sortedPalette = [...palette].sort((a, b) => a.startLayer - b.startLayer);

    /* Initialize dst with src so alpha is preserved. */
    dstPixels.set(srcPixels);

    /* Loop layer by layer (this mirrors IllumiStack's frame-by-frame
       accumulation but does it all at once). */
    for (let layer = 1; layer <= totalLayers; layer++) {
        const thresh = subd * (layer - 1);
        const activeColor = pickColorForLayer(sortedPalette, layer, totalLayers);

        if (!activeColor) continue;

        const destRgb = hexToRgb(activeColor.color);
        const mix = activeColor.mixFactor;

        for (let i = 0; i < srcPixels.length; i += 4) {
            const a = srcPixels[i + 3];
            if (a === 0) continue;

            const brightness = (srcPixels[i] + srcPixels[i + 1] + srcPixels[i + 2]) / 3;
            if (brightness < thresh) continue;

            /* Origin colour: bg on layer 1, otherwise the current dst pixel. */
            const orig = (layer === 1)
                ? bgRgb
                : [dstPixels[i], dstPixels[i + 1], dstPixels[i + 2]];

            const mixed = pigmentLerp(orig, destRgb, mix);
            dstPixels[i] = mixed[0];
            dstPixels[i + 1] = mixed[1];
            dstPixels[i + 2] = mixed[2];
        }
    }
}

/** Pick the palette entry that is "active" for a given layer (latest startLayer <= layer). */
function pickColorForLayer(sortedPalette, layer, totalLayers) {
    let chosen = null;
    for (const entry of sortedPalette) {
        if (entry.startLayer <= layer) chosen = entry;
        else break;
    }
    return chosen;
}

/* ===================================================================== */
/*  TRANSMISSION-STACKING MODE  (HueForge-style translucent filament)     */
/* ===================================================================== */

/**
 * @typedef {Object} TransmissionLayer
 * @property {string} color       hex of the filament colour
 * @property {number} startLayer  1-indexed first print layer of this colour
 * @property {number} td          transmission distance, in *layers*.
 *                                Larger TD = more translucent (light passes
 *                                through more layers before being fully absorbed).
 *                                Typical thin filament TD ≈ 4 layers @ 0.08mm.
 */

/**
 * Process an image using a transmission-distance model.
 *
 * Each pixel's brightness picks a "stop layer" — the layer at which printing
 * effectively stops over that pixel (brighter = more layers).
 * The colour the eye sees is then the *combination* of:
 *
 *    - light entering from above, passing down through the topmost layers
 *      (these are translucent → they tint the light according to their TD)
 *    - hitting the opaque base / earlier opaque layers
 *    - travelling back up out through the same translucent stack
 *
 * Implementation here is a per-layer absorption stack (Beer–Lambert style),
 * which matches HueForge's "transmission distance" mental model closely
 * enough for visual prediction.
 *
 *   layerColor(L)   = palette colour active at layer L
 *   td(L)           = transmission distance of that colour, in layers
 *   per-layer α     = 1 - exp(-1 / td)
 *                     (so after `td` layers you've absorbed ~63% of incident light)
 *
 * The accumulated colour seen for a pixel that reaches layer N is:
 *
 *   c = backgroundColor
 *   for L from 1..N:
 *       c = (1-α_L) * c + α_L * layerColor(L)
 *
 *   then for the trip back up:
 *   for L from N..1:
 *       c = (1-α_L) * c + α_L * layerColor(L)
 *
 * This is the same idea HueForge uses to predict mixed colours from
 * translucent stacks; the double pass approximates light entering and
 * re-exiting the filament.
 */
export function processTransmission(srcPixels, dstPixels, opts) {
    const { palette, backgroundColor, totalLayers } = opts;
    const bgRgb = hexToRgb(backgroundColor);
    const sortedPalette = [...palette].sort((a, b) => a.startLayer - b.startLayer);

    /* Pre-compute per-layer colour + alpha. */
    const layerColors = new Array(totalLayers + 1);
    const layerAlphas = new Array(totalLayers + 1);
    for (let L = 1; L <= totalLayers; L++) {
        const entry = pickColorForLayer(sortedPalette, L, totalLayers);
        const c = entry ? hexToRgb(entry.color) : bgRgb;
        const td = entry ? Math.max(0.25, entry.td || 4) : 4;
        layerColors[L] = c;
        layerAlphas[L] = 1 - Math.exp(-1 / td);
    }

    for (let i = 0; i < srcPixels.length; i += 4) {
        const a = srcPixels[i + 3];
        if (a === 0) {
            dstPixels[i + 3] = 0;
            continue;
        }

        const brightness = (srcPixels[i] + srcPixels[i + 1] + srcPixels[i + 2]) / 3;
        /* Brightness 0   → only 1 layer (almost no print)
           Brightness 255 → full stack */
        const stopLayer = Math.max(1, Math.round((brightness / 255) * totalLayers));

        /* Down-pass: light enters from above and travels down. */
        let r = bgRgb[0], g = bgRgb[1], b = bgRgb[2];
        for (let L = stopLayer; L >= 1; L--) {
            const c = layerColors[L];
            const α = layerAlphas[L];
            r = (1 - α) * r + α * c[0];
            g = (1 - α) * g + α * c[1];
            b = (1 - α) * b + α * c[2];
        }
        /* Up-pass: light reflects off the base and travels back out. */
        for (let L = 1; L <= stopLayer; L++) {
            const c = layerColors[L];
            const α = layerAlphas[L];
            r = (1 - α) * r + α * c[0];
            g = (1 - α) * g + α * c[1];
            b = (1 - α) * b + α * c[2];
        }

        dstPixels[i]     = r;
        dstPixels[i + 1] = g;
        dstPixels[i + 2] = b;
        dstPixels[i + 3] = a;
    }
}

/* ===================================================================== */
/*  LAYER PLAN  (for the human-readable layer table)                      */
/* ===================================================================== */

/**
 * Build a layer plan that describes which colour the user will load for
 * which physical print-layer range, plus the corresponding Z heights.
 *
 * @returns {Array<{
 *   fromLayer: number, toLayer: number,
 *   fromZ: number, toZ: number,
 *   color: string, label: string, td: number | null
 * }>}
 */
export function buildLayerPlan(opts) {
    const {
        palette, backgroundColor, totalLayers,
        layerHeight, baseLayers, compensateFirstLayer
    } = opts;

    const sortedPalette = [...palette].sort((a, b) => a.startLayer - b.startLayer);
    const plan = [];

    /* Opaque base. */
    if (baseLayers > 0) {
        plan.push({
            fromLayer: 1,
            toLayer: baseLayers,
            fromZ: 0,
            toZ: baseLayers * layerHeight,
            color: backgroundColor,
            label: 'Base / background',
            td: null
        });
    }

    /* Relief stack: assign each relief layer to its active colour. */
    let runStart = 1;
    let runEntry = pickColorForLayer(sortedPalette, 1, totalLayers);

    const baseZ = baseLayers * layerHeight + (compensateFirstLayer ? layerHeight : 0);

    for (let L = 2; L <= totalLayers + 1; L++) {
        const entry = (L <= totalLayers)
            ? pickColorForLayer(sortedPalette, L, totalLayers)
            : null;
        const sameAsPrev = entry && runEntry
            && entry.color === runEntry.color
            && (entry.td || 0) === (runEntry.td || 0);

        if (!sameAsPrev) {
            if (runEntry) {
                const from = baseLayers + runStart;
                const to = baseLayers + (L - 1);
                plan.push({
                    fromLayer: from,
                    toLayer: to,
                    fromZ: baseZ + (runStart - 1) * layerHeight,
                    toZ: baseZ + (L - 1) * layerHeight,
                    color: runEntry.color,
                    label: runEntry.label || `Colour @ layer ${runEntry.startLayer}`,
                    td: runEntry.td ?? null
                });
            }
            runStart = L;
            runEntry = entry;
        }
    }

    return plan;
}

/* ===================================================================== */
/*  HEIGHTMAP — for 3D mesh generation                                    */
/* ===================================================================== */

/**
 * Build a 2D height map (in mm) from the *source* image brightness.
 * Brighter = taller relief.
 */
export function buildHeightMap(srcPixels, width, height, opts) {
    const { totalLayers, layerHeight, baseLayers, compensateFirstLayer } = opts;
    const reliefDepth = totalLayers * layerHeight;
    const baseDepth = baseLayers * layerHeight;
    const compensation = compensateFirstLayer ? layerHeight : 0;

    const heightMap = new Float32Array(width * height);
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 4;
            const brightness = (srcPixels[idx] + srcPixels[idx + 1] + srcPixels[idx + 2]) / 3;
            heightMap[y * width + x] =
                (brightness / 255) * reliefDepth + baseDepth + compensation;
        }
    }
    return heightMap;
}
