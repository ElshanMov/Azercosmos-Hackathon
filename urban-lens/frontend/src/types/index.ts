// STAC Types
export interface Geometry {
  type: 'Point' | 'LineString' | 'Polygon' | 'MultiPoint' | 'MultiLineString' | 'MultiPolygon';
  coordinates: number[] | number[][] | number[][][];
}

export interface StacItemProperties {
  datetime?: string;
  operator?: string;
  operator_code?: string;
  operator_color?: string;
  infrastructure_type?: string;
  type_code?: string;
  category?: string;
  status?: string;
  depth_meters?: number;
  material?: string;
  building_type?: string;
  floors?: number;
  year_built?: number;
  name?: string;
  [key: string]: unknown;
}

export interface StacItem {
  type: 'Feature';
  id: string;
  geometry: Geometry;
  bbox: number[];
  properties: StacItemProperties;
  collection?: string;
}

export interface StacFeatureCollection {
  type: 'FeatureCollection';
  features: StacItem[];
  numberMatched?: number;
  numberReturned?: number;
}

export interface Operator {
  id: string;
  code: string;
  name: string;
  name_az?: string;
  category: string;
  color: string;
}

export interface InfrastructureType {
  id: string;
  code: string;
  name: string;
  name_az?: string;
  category: string;
}

export interface Stats {
  total_infrastructure: number;
  total_buildings: number;
  total_streets: number;
  operators: Array<{
    code: string;
    name: string;
    color: string;
    count: number;
  }>;
  categories: Array<{
    category: string;
    count: number;
  }>;
  bbox: number[];
}

// Filter state
export interface FilterState {
  operators: string[];
  categories: string[];
  showInfrastructure: boolean;
  showBuildings: boolean;
}
