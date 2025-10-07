import { Stop } from './stop';

export type { Stop };

export interface Route {
  id: string;
  name: string;
  code?: string;
  color?: string;
  stops: Stop[];
  active?: boolean;
}