import { Stop } from './stop';
import { DelayPrediction, LiveBusLocation } from './delay';

export interface Route {
  id: string;
  name: string;
  color?: string;
  stops: Stop[];
  busLocations?: LiveBusLocation[];  // Add this property
  delayPredictions?: DelayPrediction[];
  pathGeoJson?: any;
}
export type { Stop };

