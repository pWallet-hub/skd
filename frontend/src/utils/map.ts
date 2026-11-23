/** Base map tiles. Override with VITE_MAP_TILE_URL (e.g. a self-hosted or commercial tile server). */
export const TILE_URL =
  import.meta.env.VITE_MAP_TILE_URL ?? "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
export const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
export const DEFAULT_CENTER: [number, number] = [-1.955, 30.09];
