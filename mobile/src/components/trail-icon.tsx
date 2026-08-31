import { Image } from 'expo-image';
import React, { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { Marker } from '@/components/map';
import { Brand } from '@/constants/brand';
import { trailIconAspect } from '@/data/trail-assets';
import { LatLng } from '@/lib/geo';
import { Trail, trailIcon } from '@/lib/trails';

/** Pixel box of a sign badge — used for layout and the map's marker
 * de-overlap. `size` is the SHORT side for every sign: landscape signs get
 * height=size and a wider width; portrait signs get width=size and a taller
 * height. This keeps all icons visually the same weight on the map. */
export function badgeBox(trail: Trail, size: number): { width: number; height: number } {
  const ar = Math.min(Math.max(trailIconAspect[trail.id] ?? 0.6, 0.45), 1.9);
  if (ar >= 1) {
    return { width: Math.round(size * ar), height: size };
  }
  return { width: size, height: Math.round(size / ar) };
}

/** The sign itself, shaped like the physical plaque (no circle, no padding).
 * Same STL render as the web map. Falls back to an accent square for trails
 * without an icon yet. `dimmed` greys it out while another trail is selected. */
export function TrailIconBadge({
  trail,
  size = 38,
  selected = false,
  dimmed = false,
  onIconLoaded,
}: {
  trail: Trail;
  size?: number;
  selected?: boolean;
  dimmed?: boolean;
  onIconLoaded?: () => void;
}) {
  const icon = trailIcon(trail.id);
  const ring = selected
    ? Brand.amber
    : dimmed
      ? '#9AA09C'
      : trail.accentColor || Brand.pine;
  const { width, height } = badgeBox(trail, size);
  const radius = Math.max(3, Math.round(size * 0.08));

  if (!icon) {
    return (
      <View
        style={[
          styles.box,
          {
            width: Math.round(size * 0.7),
            height: size,
            borderRadius: radius,
            borderColor: ring,
            borderWidth: selected ? 2.5 : 1.5,
            opacity: dimmed ? 0.35 : 1,
          },
        ]}>
        <View
          style={{
            width: size / 3,
            height: size / 3,
            borderRadius: size / 6,
            backgroundColor: ring,
          }}
        />
      </View>
    );
  }

  return (
    <View
      style={[
        styles.box,
        {
          width,
          height,
          borderRadius: radius,
          borderColor: ring,
          borderWidth: selected ? 2.5 : 1.5,
          opacity: dimmed ? 0.35 : 1,
        },
      ]}>
      {/* expo-image, NOT react-native's Image: core Image never paints inside
          react-native-maps marker views on the new architecture (loads finish
          but the bitmap is never drawn), leaving white squares. */}
      <Image
        source={icon}
        style={{ width: '100%', height: '100%' }}
        contentFit="fill"
        transition={0}
        onLoadEnd={onIconLoaded}
      />
    </View>
  );
}

/** Map marker for a trail sign.
 * The marker keeps tracksViewChanges on through size/dim changes AND until
 * the icon image has actually drawn (so badges never appear blank), then
 * freezes the view for map performance. */
export function TrailMarker({
  trail,
  coordinate,
  selected,
  dimmed = false,
  size = 38,
  refresh,
  onPress,
  children,
}: {
  trail: Trail;
  coordinate: LatLng;
  selected: boolean;
  dimmed?: boolean;
  size?: number;
  /** Bump/flip this when icon bitmaps become available (e.g. after the
   * preload strip finishes) to force markers to re-snapshot their views.
   * Needed because Android never starts image loads inside detached marker
   * views — they only draw if the bitmap is already in cache. */
  refresh?: string | number | boolean;
  onPress: () => void;
  children?: React.ReactNode;
}) {
  const viewKey = `${size}|${selected}|${dimmed}|${refresh ?? ''}`;
  // Every icon load reopens a short tracking window so a late image decode
  // still gets drawn into the frozen marker snapshot.
  const [loadTick, setLoadTick] = useState(0);
  const [frozenKey, setFrozenKey] = useState('');
  const trackKey = `${viewKey}|${loadTick}`;

  useEffect(() => {
    const t = setTimeout(() => setFrozenKey(trackKey), 450);
    return () => clearTimeout(t);
  }, [trackKey]);

  return (
    <Marker
      coordinate={coordinate}
      anchor={{ x: 0.5, y: 0.5 }}
      tracksViewChanges={frozenKey !== trackKey}
      onPress={onPress}>
      <TrailIconBadge
        trail={trail}
        selected={selected}
        dimmed={dimmed}
        size={size}
        onIconLoaded={() => setLoadTick((n) => n + 1)}
      />
      {children}
    </Marker>
  );
}

const styles = StyleSheet.create({
  box: {
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 1 },
    elevation: 3,
  },
});
