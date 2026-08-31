// Native (iOS/Android) map surface. Re-exports react-native-maps as-is.
// The web build resolves map.web.tsx instead, since react-native-maps has no
// web support (it calls codegenNativeComponent at import time).
export { default } from 'react-native-maps';
export * from 'react-native-maps';
