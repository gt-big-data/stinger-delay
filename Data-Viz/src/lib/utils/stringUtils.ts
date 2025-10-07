// Capitalize the first letter of a string.
export function capitalize(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}


// Truncate a long string and append ellipsis.
export function truncate(str: string, maxLength: number): string {
  return str.length > maxLength ? str.slice(0, maxLength - 3) + '...' : str;
}
