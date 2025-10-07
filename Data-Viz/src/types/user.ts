// For future use if we have accounts or user preferences
export interface User {
  id: string;
  name?: string;
  preferences?: {
    favoriteRoutes?: string[];
  };
}
