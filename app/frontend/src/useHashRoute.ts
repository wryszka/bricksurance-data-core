import { useCallback, useEffect, useState } from 'react';

// Tiny hash router. Every view is deep-linkable:
//   #/  #/search/<term>  #/metric/<name>  #/entity/<name>
//   #/code_set/<name>  #/function/<name>  #/lineage/<kind>/<name>
//   #/governance  #/regulatory/<regime>  #/exchange  #/network  #/engineers

export interface Route {
  path: string; // raw hash minus leading "#/"
  parts: string[]; // decoded segments
}

function parseHash(): Route {
  let raw = window.location.hash || '#/';
  if (raw.startsWith('#')) raw = raw.slice(1);
  if (raw.startsWith('/')) raw = raw.slice(1);
  const parts = raw
    .split('/')
    .filter((s) => s.length > 0)
    .map((s) => {
      try {
        return decodeURIComponent(s);
      } catch {
        return s;
      }
    });
  return { path: raw, parts };
}

export function navigate(to: string) {
  const clean = to.startsWith('#') ? to : `#${to.startsWith('/') ? '' : '/'}${to}`;
  if (window.location.hash === clean) return;
  window.location.hash = clean;
}

export function href(segments: (string | number)[]): string {
  return '#/' + segments.map((s) => encodeURIComponent(String(s))).join('/');
}

export function useHashRoute(): { route: Route; go: (to: string) => void } {
  const [route, setRoute] = useState<Route>(() => parseHash());

  useEffect(() => {
    const onChange = () => {
      setRoute(parseHash());
      window.scrollTo(0, 0);
    };
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);

  const go = useCallback((to: string) => navigate(to), []);
  return { route, go };
}
