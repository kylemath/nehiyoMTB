import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';
import React from 'react';
import { ColorValue } from 'react-native';

import { usePalette } from '@/components/ui';

export default function TabsLayout() {
  const p = usePalette();

  const icon = (name: keyof typeof Ionicons.glyphMap) =>
    function TabIcon({ color, size }: { color: ColorValue; size: number }) {
      return <Ionicons name={name} color={color} size={size} />;
    };

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: p.primary,
        tabBarInactiveTintColor: p.muted,
        tabBarStyle: { backgroundColor: p.bg, borderTopColor: p.border },
      }}>
      {/* '/' is a hidden redirect to the Map tab (see index.tsx). */}
      <Tabs.Screen name="index" options={{ href: null }} />
      <Tabs.Screen name="map" options={{ title: 'Map', tabBarIcon: icon('map-outline') }} />
      <Tabs.Screen name="hunt" options={{ title: 'Hunt', tabBarIcon: icon('trophy-outline') }} />
      <Tabs.Screen name="ride" options={{ title: 'Ride', tabBarIcon: icon('bicycle-outline') }} />
      <Tabs.Screen name="ranks" options={{ title: 'Ranks', tabBarIcon: icon('podium-outline') }} />
      <Tabs.Screen
        name="profile"
        options={{ title: 'You', tabBarIcon: icon('person-circle-outline') }}
      />
    </Tabs>
  );
}
