import { Route, Stop } from './route';
import { DelayPrediction } from './delay';

export interface Trip {
  id: string;
  route: Route;
  startStop: Stop;
  endStop: Stop;
  plannedDeparture: string;   // ISO string
  plannedArrival: string;     // ISO string
  actualDeparture?: string;
  actualArrival?: string;
  delay?: DelayPrediction;
}
