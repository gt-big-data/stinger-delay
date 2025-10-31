export interface DelayPrediction {
  routeId: string;
  stopId: string;
  predictedDelayMinutes: number;
  eta: string; // ISO string
  confidence?: number; // confidence score 0–1
}

export interface LiveBusLocation {
  routeId: string;
  busId: string;
  latitude: number;
  longitude: number;
  lastUpdated: string; // ISO timestamp
}