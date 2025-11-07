// src/lib/mocks/mockTripData.ts
import { Route } from '@/types/route';

export const mockRoutes: Route[] = [
  {
    id: '1',
    name: 'Gold Route',
    color: '#b3a369',
    stops: [
      { id: 'stop1', name: 'Tech Square WB', latitude: 33.777, longitude: -84.390, sequence: 1 },
      { id: 'stop2', name: '5th Street Bridge WB', latitude: 33.777, longitude: -84.392, sequence: 2 },
      { id: 'stop3', name: 'Klaus Building EB', latitude: 33.777, longitude: -84.396, sequence: 3 }
    ],
    busLocations: [],
    delayPredictions: []
  },
  {
    id: '2',
    name: 'Red Route',
    color: '#d11c1cff',
    stops: [
      { id: 'stop4', name: 'Klaus Building WB', latitude: 33.777, longitude: -84.396, sequence: 1 },
      { id: 'stop5', name: 'Nanotechnology', latitude: 33.778, longitude: -84.398, sequence: 2 },
      { id: 'stop6', name: 'Kendeda Building', latitude: 33.778, longitude: -84.400, sequence: 3 }
    ],
    busLocations: [],
    delayPredictions: []
  }
];
