import { X, MapPin, Building2, Cable, Calendar, Ruler, Package } from 'lucide-react';

interface FeaturePanelProps {
  feature: GeoJSON.Feature | null;
  onClose: () => void;
}

export default function FeaturePanel({ feature, onClose }: FeaturePanelProps) {
  if (!feature) return null;

  const props = feature.properties || {};
  const isBuilding = props.building_type !== undefined;

  return (
    <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 w-[480px] bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden z-[1000]">
      {/* Header */}
      <div 
        className="p-4 text-white"
        style={{ backgroundColor: props.operator_color || '#3b82f6' }}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {isBuilding ? (
              <Building2 className="w-6 h-6" />
            ) : (
              <Cable className="w-6 h-6" />
            )}
            <div>
              <h3 className="font-bold text-lg">
                {props.name || props.infrastructure_type || 'Obyekt'}
              </h3>
              <p className="text-sm opacity-90">{props.operator || 'Naməlum operator'}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="grid grid-cols-2 gap-4">
          {/* Left column */}
          <div className="space-y-3">
            {isBuilding ? (
              <>
                <InfoItem
                  icon={<Building2 className="w-4 h-4 text-blue-500" />}
                  label="Bina növü"
                  value={props.building_type || 'N/A'}
                />
                {props.floors && (
                  <InfoItem
                    icon={<Ruler className="w-4 h-4 text-green-500" />}
                    label="Mərtəbə sayı"
                    value={props.floors}
                  />
                )}
                {props.year_built && (
                  <InfoItem
                    icon={<Calendar className="w-4 h-4 text-orange-500" />}
                    label="Tikiliş ili"
                    value={props.year_built}
                  />
                )}
              </>
            ) : (
              <>
                <InfoItem
                  icon={<Cable className="w-4 h-4 text-red-500" />}
                  label="İnfrastruktur növü"
                  value={props.infrastructure_type || 'N/A'}
                />
                <InfoItem
                  icon={<Package className="w-4 h-4 text-purple-500" />}
                  label="Kateqoriya"
                  value={props.category || 'N/A'}
                />
                {props.material && (
                  <InfoItem
                    icon={<Package className="w-4 h-4 text-gray-500" />}
                    label="Material"
                    value={props.material}
                  />
                )}
              </>
            )}
          </div>

          {/* Right column */}
          <div className="space-y-3">
            <InfoItem
              icon={<MapPin className="w-4 h-4 text-red-500" />}
              label="Operator"
              value={props.operator || 'N/A'}
            />
            {props.status && (
              <InfoItem
                icon={<div className={`w-3 h-3 rounded-full ${
                  props.status === 'active' ? 'bg-green-500' : 
                  props.status === 'maintenance' ? 'bg-yellow-500' : 'bg-gray-500'
                }`} />}
                label="Status"
                value={statusText(props.status)}
              />
            )}
            {props.depth_meters && (
              <InfoItem
                icon={<Ruler className="w-4 h-4 text-blue-500" />}
                label="Dərinlik"
                value={`${props.depth_meters} m`}
              />
            )}
          </div>
        </div>

        {/* STAC ID */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>STAC ID: {feature.id}</span>
            <span className="px-2 py-1 bg-gray-100 rounded text-gray-600">
              {isBuilding ? 'buildings' : 'infrastructure'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="flex items-start gap-2">
      <div className="mt-0.5">{icon}</div>
      <div>
        <div className="text-xs text-gray-500">{label}</div>
        <div className="text-sm font-medium text-gray-800">{value}</div>
      </div>
    </div>
  );
}

function statusText(status: string): string {
  const map: Record<string, string> = {
    active: 'Aktiv',
    maintenance: 'Təmirdə',
    planned: 'Planlaşdırılıb',
    decommissioned: 'İstifadədən çıxarılıb',
  };
  return map[status] || status;
}
