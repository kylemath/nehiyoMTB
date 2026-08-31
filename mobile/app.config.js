// Dynamic Expo config layered on top of app.json.
// Injects the Android Google Maps SDK key from the environment so the real key
// lives in mobile/.env (gitignored) instead of being committed. Expo CLI loads
// .env automatically when evaluating this file.
//
//   mobile/.env:  GOOGLE_MAPS_ANDROID_API_KEY=AIza...
//
// iOS uses Apple Maps and needs no key.
const { expo } = require('./app.json');

module.exports = () => {
  const apiKey = process.env.GOOGLE_MAPS_ANDROID_API_KEY;

  return {
    ...expo,
    android: {
      ...expo.android,
      config: {
        ...(expo.android?.config ?? {}),
        ...(apiKey ? { googleMaps: { apiKey } } : {}),
      },
    },
  };
};
