import { Redirect } from 'expo-router';

/** The launch URL '/' always resolves here, so this is the one reliable
 * place to choose the starting tab. Hunt first: its icon list decodes every
 * sign bitmap, so the Map tab's markers draw instantly when visited. */
export default function Index() {
  return <Redirect href="/hunt" />;
}
