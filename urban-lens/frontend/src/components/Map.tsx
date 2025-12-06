import { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import type { FilterState } from '../types';

interface MapProps {
  filters: FilterState;
  onFeatureClick?: (feature: GeoJSON.Feature) => void;
}

const BAKU_CENTER: [number, number] = [40.3690, 49.8370];
const DEFAULT_ZOOM = 15;

const CATEGORY_COLORS: Record<string, string> = {
  telecom: '#6366f1',
  water: '#06b6d4',
  gas: '#f59e0b',
  electricity: '#ef4444',
};

const BUILDING_COLORS: Record<string, string> = {
  residential: '#3b82f6',
  commercial: '#8b5cf6',
  government: '#1e293b',
  hotel: '#ec4899',
  cultural: '#14b8a6',
  museum: '#f97316',
  public_space: '#22c55e',
};

const CATEGORY_LABELS: Record<string, string> = {
  telecom: 'Telekommunikasiya',
  water: 'Su təchizatı',
  gas: 'Qaz',
  electricity: 'Elektrik',
};

const STATUS_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  active: { bg: '#dcfce7', text: '#166534', label: 'Aktiv' },
  inactive: { bg: '#fef3c7', text: '#92400e', label: 'Qeyri-aktiv' },
  maintenance: { bg: '#fee2e2', text: '#991b1b', label: 'Təmirdə' },
};

const createInfraPopup = (props: any) => {
  const statusConfig = STATUS_CONFIG[props.status] || STATUS_CONFIG.active;
  const categoryLabel = CATEGORY_LABELS[props.category] || props.category || 'N/A';
  
  return `
    <div style="font-family: 'Inter', system-ui, -apple-system, sans-serif; width: 280px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
      <div style="background: linear-gradient(135deg, ${props.operator_color || '#6366f1'} 0%, ${props.operator_color || '#6366f1'}dd 100%); padding: 16px; color: white;">
        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9; margin-bottom: 4px;">İnfrastruktur</div>
        <div style="font-size: 16px; font-weight: 600;">${props.infrastructure_type || 'Naməlum'}</div>
      </div>
      <div style="padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
          <span style="color: #64748b; font-size: 13px;">Operator</span>
          <span style="font-weight: 500; color: #1e293b; font-size: 13px;">${props.operator || 'N/A'}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
          <span style="color: #64748b; font-size: 13px;">Kateqoriya</span>
          <span style="font-weight: 500; color: #1e293b; font-size: 13px;">${categoryLabel}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
          <span style="color: #64748b; font-size: 13px;">Status</span>
          <span style="background: ${statusConfig.bg}; color: ${statusConfig.text}; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500;">${statusConfig.label}</span>
        </div>
        ${props.depth_meters ? `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
          <span style="color: #64748b; font-size: 13px;">Dərinlik</span>
          <span style="font-weight: 600; color: #6366f1; font-size: 13px;">${props.depth_meters} metr</span>
        </div>
        ` : ''}
        ${props.material ? `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
          <span style="color: #64748b; font-size: 13px;">Material</span>
          <span style="font-weight: 500; color: #1e293b; font-size: 13px;">${props.material}</span>
        </div>
        ` : ''}
      </div>
    </div>
  `;
};

const createBuildingPopup = (props: any) => {
  const fillColor = props.operator_color || BUILDING_COLORS[props.building_type] || '#3b82f6';
  
  return `
    <div style="font-family: 'Inter', system-ui, -apple-system, sans-serif; width: 280px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
      <div style="background: linear-gradient(135deg, ${fillColor} 0%, ${fillColor}dd 100%); padding: 16px; color: white;">
        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9; margin-bottom: 4px;">Bina</div>
        <div style="font-size: 16px; font-weight: 600;">${props.name || 'Adsız bina'}</div>
      </div>
      <div style="padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
          <span style="color: #64748b; font-size: 13px;">Bina növü</span>
          <span style="font-weight: 500; color: #1e293b; font-size: 13px;">${props.building_type || 'N/A'}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
          <span style="color: #64748b; font-size: 13px;">Mülkiyyətçi</span>
          <span style="font-weight: 500; color: #1e293b; font-size: 13px;">${props.operator || 'N/A'}</span>
        </div>
        ${props.floors ? `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
          <span style="color: #64748b; font-size: 13px;">Mərtəbə</span>
          <span style="font-weight: 600; color: #3b82f6; font-size: 15px;">${props.floors}</span>
        </div>
        ` : ''}
        ${props.year_built ? `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
          <span style="color: #64748b; font-size: 13px;">Tikiliş ili</span>
          <span style="font-weight: 500; color: #1e293b; font-size: 13px;">${props.year_built}</span>
        </div>
        ` : ''}
      </div>
    </div>
  `;
};

export default function Map({ filters, onFeatureClick }: MapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const infraLayerRef = useRef<L.LayerGroup | null>(null);
  const buildingLayerRef = useRef<L.LayerGroup | null>(null);
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: BAKU_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: false,
      preferCanvas: true,
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '© CARTO',
      maxZoom: 19,
    }).addTo(map);

    L.control.scale({ position: 'bottomleft', metric: true, imperial: false }).addTo(map);

    infraLayerRef.current = L.layerGroup().addTo(map);
    buildingLayerRef.current = L.layerGroup().addTo(map);

    mapRef.current = map;
    
    map.whenReady(() => setMapReady(true));

    return () => {
      map.remove();
      mapRef.current = null;
      infraLayerRef.current = null;
      buildingLayerRef.current = null;
      setMapReady(false);
    };
  }, []);

  const loadInfrastructure = useCallback(() => {
    const infraLayer = infraLayerRef.current;
    if (!infraLayer) return;

    infraLayer.clearLayers();

    if (!filters.showInfrastructure) return;

    const params = new URLSearchParams({ limit: '1000' });
    if (filters.categories.length === 1) params.append('category', filters.categories[0]);
    if (filters.operators.length === 1) params.append('operator', filters.operators[0]);

    fetch(`/api/geojson/infrastructure?${params}`)
      .then(res => res.json())
      .then((data: GeoJSON.FeatureCollection) => {
        data.features.forEach(feature => {
          if (filters.operators.length > 1 && !filters.operators.includes(feature.properties?.operator_code)) return;
          if (filters.categories.length > 1 && !filters.categories.includes(feature.properties?.category)) return;

          try {
            const geom = feature.geometry as any;
            if (!geom?.coordinates) return;

            const props = feature.properties || {};
            const color = props.operator_color || CATEGORY_COLORS[props.category] || '#6366f1';

            if (geom.type === 'LineString' && geom.coordinates.length >= 2) {
              const latLngs = geom.coordinates.map((c: number[]) => L.latLng(c[1], c[0]));
              const line = L.polyline(latLngs, { 
                color, 
                weight: 4, 
                opacity: 0.9,
                lineCap: 'round',
                lineJoin: 'round'
              });
              line.bindPopup(createInfraPopup(props), { 
                maxWidth: 320, 
                className: 'custom-popup',
                closeButton: true 
              });
              line.on('mouseover', function() { 
                this.setStyle({ weight: 6, opacity: 1 }); 
              });
              line.on('mouseout', function() { 
                this.setStyle({ weight: 4, opacity: 0.9 }); 
              });
              line.addTo(infraLayer);
            } else if (geom.type === 'Point' && geom.coordinates.length >= 2) {
              const marker = L.circleMarker(L.latLng(geom.coordinates[1], geom.coordinates[0]), {
                radius: 8, 
                color: '#fff',
                weight: 2,
                fillColor: color, 
                fillOpacity: 0.9
              });
              marker.bindPopup(createInfraPopup(props), { maxWidth: 320 });
              marker.addTo(infraLayer);
            }
          } catch (e) {}
        });
      })
      .catch(console.error);
  }, [filters.showInfrastructure, filters.operators, filters.categories]);

  const loadBuildings = useCallback(() => {
    const buildingLayer = buildingLayerRef.current;
    if (!buildingLayer) return;

    buildingLayer.clearLayers();

    if (!filters.showBuildings) return;

    fetch(`/api/geojson/buildings?limit=500`)
      .then(res => res.json())
      .then((data: GeoJSON.FeatureCollection) => {
        data.features.forEach(feature => {
          if (filters.operators.length > 0 && !filters.operators.includes(feature.properties?.operator_code)) return;

          try {
            const geom = feature.geometry as any;
            if (!geom?.coordinates) return;

            const props = feature.properties || {};
            const fillColor = props.operator_color || BUILDING_COLORS[props.building_type] || '#3b82f6';

            if (geom.type === 'Polygon' && geom.coordinates[0]?.length >= 4) {
              const latLngs = geom.coordinates[0].map((c: number[]) => L.latLng(c[1], c[0]));
              const poly = L.polygon(latLngs, { 
                color: '#fff', 
                weight: 2, 
                fillColor, 
                fillOpacity: 0.7 
              });
              poly.bindPopup(createBuildingPopup(props), { maxWidth: 320 });
              poly.on('mouseover', function() { 
                this.setStyle({ fillOpacity: 0.9, weight: 3 }); 
              });
              poly.on('mouseout', function() { 
                this.setStyle({ fillOpacity: 0.7, weight: 2 }); 
              });
              poly.addTo(buildingLayer);
            } else if (geom.type === 'Point' && geom.coordinates.length >= 2) {
              const marker = L.circleMarker(L.latLng(geom.coordinates[1], geom.coordinates[0]), {
                radius: 10, 
                color: '#fff', 
                weight: 2,
                fillColor, 
                fillOpacity: 0.8
              });
              marker.bindPopup(createBuildingPopup(props), { maxWidth: 320 });
              marker.addTo(buildingLayer);
            }
          } catch (e) {}
        });
      })
      .catch(console.error);
  }, [filters.showBuildings, filters.operators]);

  useEffect(() => {
    if (!mapReady) return;
    loadInfrastructure();
    loadBuildings();
  }, [mapReady, loadInfrastructure, loadBuildings]);

  return <div ref={containerRef} className="w-full h-full" style={{ minHeight: '400px' }} />;
}
