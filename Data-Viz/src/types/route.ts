import { Stop } from './stop';
import { DelayPrediction, LiveBusLocation } from './delay';

export type { Stop, LiveBusLocation, DelayPrediction };
 
export interface Route {
  id: string;
  name: string;
  color?: string;
  stops: Stop[];
  busLocations?: LiveBusLocation[];
  delayPredictions?: DelayPrediction[];
  active?: boolean;
  pathGeoJson?: any;
}
