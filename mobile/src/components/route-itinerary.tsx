import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { TrailIconBadge } from '@/components/trail-icon';
import { usePalette } from '@/components/ui';
import { Brand } from '@/constants/brand';
import { formatKm } from '@/lib/geo';
import { BikeRoute } from '@/lib/routing';
import { displayName, trailById } from '@/lib/trails';

const MIN_CONNECTOR_M = 25;
const RAIL_WIDTH = 36;
const RAIL_WIDTH_COMPACT = 20;

const DIFFICULTY_COLORS: Record<string, string> = {
  green: Brand.moss,
  blue: '#2B6CB0',
};

/** Ski-style difficulty marker: green circle, blue square, black diamond,
 * double black diamond. Icon only, no label. Null for unknown tokens. */
export function DifficultyBadge({ difficulty }: { difficulty: string | null | undefined }) {
  const p = usePalette();
  // Black reads as paper-white in dark mode, like ski trail maps on dark signage.
  const black = p.dark ? Brand.paper : Brand.ink;

  switch (difficulty) {
    case 'green':
      return (
        <View
          style={{
            width: 13,
            height: 13,
            borderRadius: 7,
            backgroundColor: DIFFICULTY_COLORS.green,
          }}
        />
      );
    case 'blue':
      return (
        <View
          style={{
            width: 12,
            height: 12,
            borderRadius: 2,
            backgroundColor: DIFFICULTY_COLORS.blue,
          }}
        />
      );
    case 'black':
      return (
        <View style={styles.diamondBox}>
          <View style={[styles.diamond, { backgroundColor: black }]} />
        </View>
      );
    case 'dblblack':
      return (
        <View style={styles.diamondRow}>
          <View style={styles.diamondBox}>
            <View style={[styles.diamond, { backgroundColor: black }]} />
          </View>
          <View style={[styles.diamondBox, { marginLeft: -3 }]}>
            <View style={[styles.diamond, { backgroundColor: black }]} />
          </View>
        </View>
      );
    default:
      return null;
  }
}

function TerminusRow({
  label,
  color,
  compact,
}: {
  label: string;
  color: string;
  compact: boolean;
}) {
  const p = usePalette();
  return (
    <View style={[styles.row, compact && styles.rowCompact]}>
      <View style={[styles.rail, compact && styles.railCompact]}>
        <View style={[compact ? styles.terminusDotCompact : styles.terminusDot, { backgroundColor: color }]} />
      </View>
      <Text style={[compact ? styles.terminusLabelCompact : styles.terminusLabel, { color: p.text }]}>
        {label}
      </Text>
    </View>
  );
}

function ConnectorRow({
  distanceM,
  active,
  done,
  compact,
}: {
  distanceM: number;
  active: boolean;
  done: boolean;
  compact: boolean;
}) {
  const p = usePalette();
  return (
    <View
      style={[
        styles.row,
        compact && styles.rowCompact,
        compact ? styles.connectorRowCompact : styles.connectorRow,
        active && styles.activeRow,
        done && styles.doneRow,
      ]}>
      <View style={[styles.rail, compact && styles.railCompact]}>
        <View style={styles.dashColumn}>
          <View style={[styles.dash, { backgroundColor: p.muted }]} />
          <View style={[styles.dash, { backgroundColor: p.muted }]} />
          {!compact && <View style={[styles.dash, { backgroundColor: p.muted }]} />}
        </View>
      </View>
      <Text
        style={[
          compact ? styles.connectorLabelCompact : styles.connectorLabel,
          { color: active ? p.text : p.muted },
        ]}>
        ride {formatKm(distanceM)}
      </Text>
    </View>
  );
}

function TrailRow({
  order,
  trailId,
  title,
  distanceM,
  active,
  done,
  compact,
}: {
  order: number;
  trailId: string;
  title: string;
  distanceM: number;
  active: boolean;
  done: boolean;
  compact: boolean;
}) {
  const p = usePalette();
  const trail = trailById(trailId);
  const dotColor = done ? Brand.moss : active ? Brand.amber : p.primary;
  return (
    <View
      style={[
        styles.row,
        compact && styles.rowCompact,
        compact ? styles.trailRowCompact : styles.trailRow,
        active && styles.activeRow,
        done && styles.doneRow,
      ]}>
      <View style={[styles.rail, compact && styles.railCompact]}>
        <View
          style={[
            compact ? styles.orderDotCompact : styles.orderDot,
            { borderColor: dotColor },
            done && { backgroundColor: Brand.moss, borderColor: Brand.moss },
          ]}>
          <Text
            style={[
              compact ? styles.orderTextCompact : styles.orderText,
              { color: done ? '#fff' : dotColor },
            ]}>
            {done ? '✓' : order}
          </Text>
        </View>
      </View>
      {trail ? <TrailIconBadge trail={trail} size={compact ? 20 : 32} /> : null}
      <View style={styles.trailInfo}>
        <View style={styles.nameRow}>
          <Text
            style={[compact ? styles.trailNameCompact : styles.trailName, { color: p.text }]}
            numberOfLines={compact ? 1 : 2}>
            {trail ? displayName(trail) : title}
          </Text>
          {!compact && <DifficultyBadge difficulty={trail?.difficulty} />}
        </View>
        <Text style={[compact ? styles.trailMetaCompact : styles.trailMeta, { color: p.muted }]}>
          {formatKm(distanceM)}
        </Text>
      </View>
    </View>
  );
}

/** Transit-directions style breakdown of a bike route: start, numbered trail
 * legs joined by dashed ride connectors, destination. Plain Views only — the
 * parent (e.g. a bottom sheet) owns scrolling.
 *
 * `activeLegIndex` marks the leg currently being ridden; legs before it show
 * as done (green check, faded). `compact` shrinks everything to fit a narrow
 * overlay column during live navigation. */
export function RouteItinerary({
  route,
  activeLegIndex,
  compact = false,
}: {
  route: BikeRoute;
  activeLegIndex?: number | null;
  compact?: boolean;
}) {
  const rows: React.ReactNode[] = [];
  let order = 0;
  route.legs.forEach((leg, i) => {
    const active = activeLegIndex === i;
    const done = activeLegIndex != null && i < activeLegIndex;
    if (leg.type === 'connector') {
      if (leg.distanceM >= MIN_CONNECTOR_M) {
        rows.push(
          <ConnectorRow
            key={`leg-${i}`}
            distanceM={leg.distanceM}
            active={active}
            done={done}
            compact={compact}
          />,
        );
      }
    } else {
      order += 1;
      rows.push(
        <TrailRow
          key={`leg-${i}`}
          order={order}
          trailId={leg.trailId}
          title={leg.title}
          distanceM={leg.distanceM}
          active={active}
          done={done}
          compact={compact}
        />,
      );
    }
  });

  return (
    <View style={styles.container}>
      <TerminusRow label="Start" color={Brand.moss} compact={compact} />
      {rows}
      <TerminusRow label="Destination" color={Brand.ember} compact={compact} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 1 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  rowCompact: { gap: 6 },
  rail: {
    width: RAIL_WIDTH,
    alignItems: 'center',
  },
  railCompact: { width: RAIL_WIDTH_COMPACT },
  terminusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  terminusDotCompact: {
    width: 9,
    height: 9,
    borderRadius: 4.5,
  },
  terminusLabel: { fontSize: 15, fontWeight: '700' },
  terminusLabelCompact: { fontSize: 12, fontWeight: '700' },
  connectorRow: {
    paddingVertical: 2,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  connectorRowCompact: {
    paddingVertical: 1,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  dashColumn: { gap: 3, alignItems: 'center' },
  dash: {
    width: 2.5,
    height: 5,
    borderRadius: 1.25,
  },
  connectorLabel: { fontSize: 13 },
  connectorLabelCompact: { fontSize: 10 },
  trailRow: {
    paddingVertical: 4,
    paddingRight: 8,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  trailRowCompact: {
    paddingVertical: 2,
    paddingRight: 4,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  activeRow: {
    borderColor: Brand.amber,
    backgroundColor: `${Brand.amber}22`,
  },
  doneRow: { opacity: 0.55 },
  orderDot: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  orderDotCompact: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  orderText: { fontSize: 12, fontWeight: '700' },
  orderTextCompact: { fontSize: 9, fontWeight: '700' },
  trailInfo: { flex: 1, gap: 1 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  trailName: { fontSize: 15, fontWeight: '600', flexShrink: 1 },
  trailNameCompact: { fontSize: 12, fontWeight: '600', flexShrink: 1 },
  trailMeta: { fontSize: 13 },
  trailMetaCompact: { fontSize: 10 },
  diamondRow: { flexDirection: 'row', alignItems: 'center' },
  diamondBox: {
    width: 14,
    height: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  diamond: {
    width: 9,
    height: 9,
    transform: [{ rotate: '45deg' }],
  },
});
