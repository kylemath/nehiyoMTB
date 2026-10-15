import { Linking, Platform } from 'react-native';

import { LatLng } from '@/lib/geo';

/** Hand off to the phone's maps app for cycling directions — a secondary
 * escape hatch next to the in-app route builder. */
export function openDirections(to: LatLng) {
  const { latitude: lat, longitude: lng } = to;
  const web = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=bicycling`;
  const url = Platform.select({
    ios: `maps:?daddr=${lat},${lng}&dirflg=b`,
    android: `google.navigation:q=${lat},${lng}&mode=b`,
    default: web,
  });
  Linking.openURL(url).catch(() => Linking.openURL(web));
}
