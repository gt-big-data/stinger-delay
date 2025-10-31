import axios from 'axios';

const ORS_API_KEY = process.env.REACT_APP_ORS_API_KEY;  // store your key in .env
const ORS_BASE_URL = 'https://api.openrouteservice.org';

export interface DirectionsResponse {
  features: {
    geometry: {
      coordinates: [number, number][];
    };
  }[];
}

export interface MatrixResponse {
  durations?: number[][];    // in seconds
  distances?: number[][];    // in meters
  // maybe other fields
}

export async function fetchRouteGeometry(
  coordinates: [number, number][],
  profile: string = 'driving-car'
): Promise<[number, number][]> {
  const url = `${ORS_BASE_URL}/v2/directions/${profile}/geojson`;
  const resp = await axios.post<DirectionsResponse>(url, {
    coordinates,
    // potentially other params like format, instructions: false, etc.
  }, {
    headers: {
      Authorization: ORS_API_KEY,
      'Content-Type': 'application/json'
    }
  });
  const geometry = resp.data.features[0].geometry.coordinates;
  // Note: coordinates from ORS are [lon, lat]. Convert to [lat, lon]
  return geometry.map(([lon, lat]) => [lat, lon]);
}

export async function fetchTimeMatrix(
  locations: [number, number][],   // list of [longitude, latitude]
  profile: string = 'driving-car',
  metrics: ('duration' | 'distance')[] = ['duration']
): Promise<MatrixResponse> {
  const url = `${ORS_BASE_URL}/v2/matrix/${profile}`;
  const resp = await axios.post<MatrixResponse>(url, {
    locations,
    metrics
  }, {
    headers: {
      Authorization: ORS_API_KEY,
      'Content-Type': 'application/json'
    }
  });
  return resp.data;
}
