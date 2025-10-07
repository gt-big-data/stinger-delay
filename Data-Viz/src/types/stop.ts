export interface Stop {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  sequence?: number; // order within a route
}
