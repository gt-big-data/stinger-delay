import { Stop } from './stop';
import { LiveBusLocation } from './delay';
import { DelayPrediction } from './delay';

export type { Stop, LiveBusLocation, DelayPrediction };
 
export interface Route {
  id: string;
  name: string;
  code?: string;
  color?: string;
  stops: Stop[];
  busLocations?: LiveBusLocation[];
  delayPredictions?: DelayPrediction[];
  active?: boolean;
  pathGeoJson?: any; // optional geometry for map (GeoJSON or coordinates[])
}
