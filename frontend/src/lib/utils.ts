import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Backend API base URL
export const API_BASE_URL = 'http://localhost:8000/api/v1';

// Utility function for making API requests
// Note: Since there's no auth token in the response, this is just a regular fetch
export async function authenticatedFetch(
  endpoint: string, 
  options: RequestInit = {}
): Promise<Response> {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  return fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
}
