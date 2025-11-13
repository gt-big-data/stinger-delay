// src/lib/mocks/mockTripData.ts
import { Route } from '@/types/route';

// Helper function to generate dynamic ETA
const generateETA = (delayMinutes: number): string => {
  const now = new Date();
  now.setMinutes(now.getMinutes() + delayMinutes);
  
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;
  const displayMinutes = minutes < 10 ? `0${minutes}` : minutes;
  
  return `${displayHours}:${displayMinutes} ${ampm}`;
};

export const mockRoutes: Route[] = [
  {
    id: '1',
    name: 'Gold Route',
    color: '#b3a369',
    stops: [
      { id: 'stop1', name: 'Tech Square WB', latitude: 33.7764, longitude: -84.3889, sequence: 1 },
      { id: 'stop2', name: '5th Street Bridge WB', latitude: 33.7775, longitude: -84.3910, sequence: 2 },
      { id: 'stop3', name: 'Klaus Building EB', latitude: 33.7772, longitude: -84.3956, sequence: 3 },
      { id: 'stop4', name: 'Student Center', latitude: 33.7738, longitude: -84.3986, sequence: 4 },
      { id: 'stop5', name: 'Midtown MARTA Station', latitude: 33.7812, longitude: -84.3867, sequence: 5 },
      { id: 'stop6', name: 'Publix Spring St', latitude: 33.7800, longitude: -84.3850, sequence: 6 },
      { id: 'stop7', name: 'Weber Turnaround', latitude: 33.7725, longitude: -84.3951, sequence: 7 }
    ],
    busLocations: [
      {
        busId: 'gold-bus-1', latitude: 33.7780, longitude: -84.3890,
        routeId: '',
        lastUpdated: ''
      }
    ],
    delayPredictions: [
      { stopId: 'stop1', predictedDelayMinutes: 4, routeId: '1', eta: generateETA(4) },
      { stopId: 'stop2', predictedDelayMinutes: 6, routeId: '1', eta: generateETA(6) },
      { stopId: 'stop3', predictedDelayMinutes: 8, routeId: '1', eta: generateETA(8) },
      { stopId: 'stop4', predictedDelayMinutes: 10, routeId: '1', eta: generateETA(10) },
      { stopId: 'stop5', predictedDelayMinutes: 15, routeId: '1', eta: generateETA(15) },
      { stopId: 'stop6', predictedDelayMinutes: 18, routeId: '1', eta: generateETA(18) },
      { stopId: 'stop7', predictedDelayMinutes: 22, routeId: '1', eta: generateETA(22) }
    ]
  },
  {
    id: '2',
    name: 'Red Route',
    color: '#d11c1cff',
    stops: [
      { id: 'stop8', name: 'Klaus Building WB', latitude: 33.7772, longitude: -84.3956, sequence: 1 },
      { id: 'stop9', name: 'Nanotechnology', latitude: 33.7783, longitude: -84.3994, sequence: 2 },
      { id: 'stop10', name: 'Kendeda Building', latitude: 33.7773, longitude: -84.4005, sequence: 3 },
      { id: 'stop11', name: 'Curran Parking Deck', latitude: 33.7795, longitude: -84.4010, sequence: 4 },
      { id: 'stop12', name: 'Van Leer', latitude: 33.7758, longitude: -84.3968, sequence: 5 },
      { id: 'stop13', name: 'Instructional Center', latitude: 33.7754, longitude: -84.3982, sequence: 6 },
      { id: 'stop14', name: 'College of Computing', latitude: 33.7778, longitude: -84.3975, sequence: 7 },
      { id: 'stop15', name: 'Howey Physics', latitude: 33.7775, longitude: -84.3990, sequence: 8 }
    ],
    busLocations: [
      {
        busId: 'red-bus-1', latitude: 33.7765, longitude: -84.3970,
        routeId: '',
        lastUpdated: ''
      }
    ],
    delayPredictions: [
      { stopId: 'stop8', predictedDelayMinutes: 3, routeId: '2', eta: generateETA(3) },
      { stopId: 'stop9', predictedDelayMinutes: 5, routeId: '2', eta: generateETA(5) },
      { stopId: 'stop10', predictedDelayMinutes: 7, routeId: '2', eta: generateETA(7) },
      { stopId: 'stop11', predictedDelayMinutes: 10, routeId: '2', eta: generateETA(10) },
      { stopId: 'stop12', predictedDelayMinutes: 13, routeId: '2', eta: generateETA(13) },
      { stopId: 'stop13', predictedDelayMinutes: 15, routeId: '2', eta: generateETA(15) },
      { stopId: 'stop14', predictedDelayMinutes: 17, routeId: '2', eta: generateETA(17) },
      { stopId: 'stop15', predictedDelayMinutes: 19, routeId: '2', eta: generateETA(19) }
    ]
  },
  {
    id: '3',
    name: 'Blue Route',
    color: '#3B82F6',
    stops: [
      { id: 'stop16', name: 'Student Center', latitude: 33.7738, longitude: -84.3986, sequence: 1 },
      { id: 'stop17', name: 'Library', latitude: 33.7746, longitude: -84.3967, sequence: 2 },
      { id: 'stop18', name: 'Skiles Classroom', latitude: 33.7741, longitude: -84.3955, sequence: 3 },
      { id: 'stop19', name: 'Weber Space Science', latitude: 33.7725, longitude: -84.3951, sequence: 4 },
      { id: 'stop20', name: 'Ferst Center', latitude: 33.7732, longitude: -84.3977, sequence: 5 },
      { id: 'stop21', name: 'Campus Recreation Center', latitude: 33.7758, longitude: -84.4025, sequence: 6 },
      { id: 'stop22', name: 'North Avenue Apartments', latitude: 33.7780, longitude: -84.4035, sequence: 7 }
    ],
    busLocations: [
      {
        busId: 'blue-bus-1', latitude: 33.7750, longitude: -84.3980,
        routeId: '',
        lastUpdated: ''
      }
    ],
    delayPredictions: [
      { stopId: 'stop16', predictedDelayMinutes: 2, routeId: '3', eta: generateETA(2) },
      { stopId: 'stop17', predictedDelayMinutes: 4, routeId: '3', eta: generateETA(4) },
      { stopId: 'stop18', predictedDelayMinutes: 6, routeId: '3', eta: generateETA(6) },
      { stopId: 'stop19', predictedDelayMinutes: 8, routeId: '3', eta: generateETA(8) },
      { stopId: 'stop20', predictedDelayMinutes: 10, routeId: '3', eta: generateETA(10) },
      { stopId: 'stop21', predictedDelayMinutes: 14, routeId: '3', eta: generateETA(14) },
      { stopId: 'stop22', predictedDelayMinutes: 17, routeId: '3', eta: generateETA(17) }
    ]
  },
  {
    id: '4',
    name: 'Green Route',
    color: '#10B981',
    stops: [
      { id: 'stop23', name: 'Student Center', latitude: 33.7738, longitude: -84.3986, sequence: 1 },
      { id: 'stop24', name: 'Bobby Dodd Stadium', latitude: 33.7722, longitude: -84.3922, sequence: 2 },
      { id: 'stop25', name: 'East Campus Apartments', latitude: 33.7705, longitude: -84.3880, sequence: 3 },
      { id: 'stop26', name: 'Techwood Drive', latitude: 33.7695, longitude: -84.3850, sequence: 4 },
      { id: 'stop27', name: 'GTRI', latitude: 33.7820, longitude: -84.3870, sequence: 5 },
      { id: 'stop28', name: 'Georgia Tech Hotel', latitude: 33.7763, longitude: -84.3878, sequence: 6 }
    ],
    busLocations: [
      {
        busId: 'green-bus-1', latitude: 33.7710, longitude: -84.3900,
        routeId: '',
        lastUpdated: ''
      }
    ],
    delayPredictions: [
      { stopId: 'stop23', predictedDelayMinutes: 6, routeId: '4', eta: generateETA(6) },
      { stopId: 'stop24', predictedDelayMinutes: 8, routeId: '4', eta: generateETA(8) },
      { stopId: 'stop25', predictedDelayMinutes: 12, routeId: '4', eta: generateETA(12) },
      { stopId: 'stop26', predictedDelayMinutes: 16, routeId: '4', eta: generateETA(16) },
      { stopId: 'stop27', predictedDelayMinutes: 20, routeId: '4', eta: generateETA(20) },
      { stopId: 'stop28', predictedDelayMinutes: 23, routeId: '4', eta: generateETA(23) }
    ]
  },
  {
    id: '5',
    name: 'Trolley Route',
    color: '#8B5CF6',
    stops: [
      { id: 'stop29', name: 'Clough Commons', latitude: 33.7751, longitude: -84.3963, sequence: 1 },
      { id: 'stop30', name: 'Kendeda Building', latitude: 33.7773, longitude: -84.4005, sequence: 2 },
      { id: 'stop31', name: 'Campus Recreation Center', latitude: 33.7758, longitude: -84.4025, sequence: 3 },
      { id: 'stop32', name: 'Tech Square', latitude: 33.7764, longitude: -84.3889, sequence: 4 },
      { id: 'stop33', name: 'Midtown MARTA', latitude: 33.7812, longitude: -84.3867, sequence: 5 },
      { id: 'stop34', name: 'Manufacture Building', latitude: 33.7765, longitude: -84.4015, sequence: 6 }
    ],
    busLocations: [
      {
        busId: 'trolley-bus-1', latitude: 33.7760, longitude: -84.3950,
        routeId: '',
        lastUpdated: ''
      }
    ],
    delayPredictions: [
      { stopId: 'stop29', predictedDelayMinutes: 5, routeId: '5', eta: generateETA(5) },
      { stopId: 'stop30', predictedDelayMinutes: 7, routeId: '5', eta: generateETA(7) },
      { stopId: 'stop31', predictedDelayMinutes: 10, routeId: '5', eta: generateETA(10) },
      { stopId: 'stop32', predictedDelayMinutes: 14, routeId: '5', eta: generateETA(14) },
      { stopId: 'stop33', predictedDelayMinutes: 18, routeId: '5', eta: generateETA(18) },
      { stopId: 'stop34', predictedDelayMinutes: 20, routeId: '5', eta: generateETA(20) }
    ]
  }
];
