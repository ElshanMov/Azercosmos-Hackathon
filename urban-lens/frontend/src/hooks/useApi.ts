import { useQuery } from '@tanstack/react-query';
import type { StacFeatureCollection, Operator, InfrastructureType, Stats } from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => fetchJson<Stats>(`${API_BASE}/stats`),
    staleTime: 30000,
  });
}

export function useOperators() {
  return useQuery({
    queryKey: ['operators'],
    queryFn: () => fetchJson<Operator[]>(`${API_BASE}/operators`),
    staleTime: 60000,
  });
}

export function useInfrastructureTypes() {
  return useQuery({
    queryKey: ['infrastructure-types'],
    queryFn: () => fetchJson<InfrastructureType[]>(`${API_BASE}/infrastructure-types`),
    staleTime: 60000,
  });
}

export function useGeoJson(
  collection: 'infrastructure' | 'buildings',
  options?: {
    bbox?: string;
    operator?: string;
    category?: string;
    enabled?: boolean;
  }
) {
  const params = new URLSearchParams();
  if (options?.bbox) params.append('bbox', options.bbox);
  if (options?.operator) params.append('operator', options.operator);
  if (options?.category) params.append('category', options.category);
  params.append('limit', '1000');

  const queryString = params.toString();
  const url = `${API_BASE}/geojson/${collection}${queryString ? `?${queryString}` : ''}`;

  return useQuery({
    queryKey: ['geojson', collection, options],
    queryFn: () => fetchJson<GeoJSON.FeatureCollection>(url),
    staleTime: 10000,
    enabled: options?.enabled !== false,
  });
}

export function useStacSearch(params: {
  collections?: string[];
  bbox?: number[];
  operator?: string;
  category?: string;
  limit?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params.collections) searchParams.append('collections', params.collections.join(','));
  if (params.bbox) searchParams.append('bbox', params.bbox.join(','));
  if (params.operator) searchParams.append('operator', params.operator);
  if (params.category) searchParams.append('category', params.category);
  searchParams.append('limit', String(params.limit || 100));

  return useQuery({
    queryKey: ['stac-search', params],
    queryFn: () => fetchJson<StacFeatureCollection>(`${API_BASE}/stac/search?${searchParams}`),
    staleTime: 10000,
  });
}
