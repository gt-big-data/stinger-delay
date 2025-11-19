import { Route } from '@/types/route';

const SHARED = {
  studentCenter:  { id: 'student-center', name: 'Student Center', latitude: 33.7738, longitude: -84.3986 },
  klaus:          { id: 'klaus', name: 'Klaus Building', latitude: 33.7772, longitude: -84.3956 },
  kendeda:        { id: 'kendeda', name: 'Kendeda Building', latitude: 33.7773, longitude: -84.4005 },
  crc:            { id: 'crc', name: 'Campus Recreation Center', latitude: 33.7758, longitude: -84.4025 },
  midtownMarta:   { id: 'midtown-marta', name: 'Midtown MARTA Station', latitude: 33.7812, longitude: -84.3867 },
  techSquare:     { id: 'tech-square', name: 'Tech Square', latitude: 33.7764, longitude: -84.3889 },
};

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
      SHARED.midtownMarta,
      { id: 'publix', name: 'Publix Spring St', latitude: 33.7800, longitude: -84.3850 },
      SHARED.techSquare,
      { id: '5th-street-bridge', name: '5th Street Bridge', latitude: 33.7775, longitude: -84.3910 },
      SHARED.klaus,
      SHARED.studentCenter,
      { id: 'weber-turnaround', name: 'Weber Turnaround', latitude: 33.7725, longitude: -84.3951 }
    ],
    busLocations: [{
      busId: 'gold-bus-1', latitude: 33.7780, longitude: -84.3890,
      routeId: '',
      lastUpdated: ''
    }],
    delayPredictions: [
      { stopId: 'midtown-marta', predictedDelayMinutes: 2, routeId: '1', eta: generateETA(2) },
      { stopId: 'tech-square', predictedDelayMinutes: 6, routeId: '1', eta: generateETA(6) },
      { stopId: 'klaus', predictedDelayMinutes: 10, routeId: '1', eta: generateETA(10) },
      { stopId: 'student-center', predictedDelayMinutes: 12, routeId: '1', eta: generateETA(12) },
      { stopId: 'weber-turnaround', predictedDelayMinutes: 15, routeId: '1', eta: generateETA(15) }
    ]
  },
  {
    id: '2',
    name: 'Red Route',
    color: '#d11c1cff',
    stops: [
      SHARED.klaus,
      { id: 'nanotechnology', name: 'Nanotechnology', latitude: 33.7783, longitude: -84.3994 },
      SHARED.kendeda,
      { id: 'curran', name: 'Curran Parking Deck', latitude: 33.7778, longitude: -84.4058 },
      SHARED.crc,
      { id: 'van-leer', name: 'Van Leer', latitude: 33.7758, longitude: -84.3968 },
      { id: 'instructional-center', name: 'Instructional Center', latitude: 33.7754, longitude: -84.3982 },
      { id: 'college-of-computing', name: 'College of Computing', latitude: 33.7778, longitude: -84.3975 },
      { id: 'howey-physics', name: 'Howey Physics', latitude: 33.7775, longitude: -84.3990 },
      SHARED.studentCenter
    ],
    busLocations: [{
      busId: 'red-bus-1', latitude: 33.7765, longitude: -84.3970,
      routeId: '',
      lastUpdated: ''
    }],
    delayPredictions: [
      { stopId: 'klaus', predictedDelayMinutes: 2, routeId: '2', eta: generateETA(2) },
      { stopId: 'kendeda', predictedDelayMinutes: 5, routeId: '2', eta: generateETA(5) },
      { stopId: 'curran', predictedDelayMinutes: 7, routeId: '2', eta: generateETA(7) },
      { stopId: 'student-center', predictedDelayMinutes: 17, routeId: '2', eta: generateETA(17) }
    ]
  },
  {
    id: '3',
    name: 'Blue Route',
    color: '#3B82F6',
    stops: [
      SHARED.studentCenter,
      { id: 'library', name: 'Library', latitude: 33.7746, longitude: -84.3967 },
      { id: 'skiles', name: 'Skiles Classroom', latitude: 33.7741, longitude: -84.3955 },
      { id: 'weber-space', name: 'Weber Space Science', latitude: 33.7725, longitude: -84.3951 },
      { id: 'ferst-center', name: 'Ferst Center', latitude: 33.7732, longitude: -84.3977 },
      SHARED.crc,
      { id: 'north-ave-apts', name: 'North Avenue Apartments', latitude: 33.7696, longitude: -84.3910 }
    ],
    busLocations: [{
      busId: 'blue-bus-1', latitude: 33.7750, longitude: -84.3980,
      routeId: '',
      lastUpdated: ''
    }],
    delayPredictions: [
      { stopId: 'student-center', predictedDelayMinutes: 2, routeId: '3', eta: generateETA(2) },
      { stopId: 'crc', predictedDelayMinutes: 14, routeId: '3', eta: generateETA(14) }
    ]
  },
  {
    id: '4',
    name: 'Green Route',
    color: '#10B981',
    stops: [
      SHARED.studentCenter,
      { id: 'bobby-dodd', name: 'Bobby Dodd Stadium', latitude: 33.7722, longitude: -84.3922 },
      { id: 'east-campus-apts', name: 'East Campus Apartments', latitude: 33.7705, longitude: -84.3880 },
      { id: 'techwood-drive', name: 'Techwood Drive', latitude: 33.7695, longitude: -84.3850 },
      { id: 'gtri', name: 'GTRI', latitude: 33.7820, longitude: -84.3870 },
      { id: 'ga-tech-hotel', name: 'Georgia Tech Hotel', latitude: 33.7763, longitude: -84.3878 }
    ],
    busLocations: [{
      busId: 'green-bus-1', latitude: 33.7710, longitude: -84.3900,
      routeId: '',
      lastUpdated: ''
    }],
    delayPredictions: [
      { stopId: 'student-center', predictedDelayMinutes: 6, routeId: '4', eta: generateETA(6) }
    ]
  },
  {
    id: '5',
    name: 'Trolley Route',
    color: '#8B5CF6',
    stops: [
      { id: 'clough', name: 'Clough Commons', latitude: 33.7751, longitude: -84.3963 },
      SHARED.kendeda,
      SHARED.crc,
      SHARED.techSquare,
      SHARED.midtownMarta,
      { id: 'manufacture-building', name: 'Manufacture Building', latitude: 33.7765, longitude: -84.4015 }
    ],
    busLocations: [{
      busId: 'trolley-bus-1', latitude: 33.7760, longitude: -84.3950,
      routeId: '',
      lastUpdated: ''
    }],
    delayPredictions: [
      { stopId: 'clough', predictedDelayMinutes: 5, routeId: '5', eta: generateETA(5) },
      { stopId: 'kendeda', predictedDelayMinutes: 7, routeId: '5', eta: generateETA(7) },
      { stopId: 'crc', predictedDelayMinutes: 10, routeId: '5', eta: generateETA(10) }
    ]
  }
];
