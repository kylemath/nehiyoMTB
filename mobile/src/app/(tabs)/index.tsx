import { Redirect } from 'expo-router';

/** The launch URL '/' always resolves here: open on the map. */
export default function Index() {
  return <Redirect href="/map" />;
}
