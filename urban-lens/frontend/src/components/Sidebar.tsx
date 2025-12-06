import { useState } from 'react';
import { 
  Layers, Building2, Cable, Droplets, Flame, Zap, 
  ChevronDown, ChevronRight, Filter, X, Map as MapIcon
} from 'lucide-react';
import type { FilterState, Operator, Stats } from '../types';

interface SidebarProps {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
  operators: Operator[];
  stats: Stats | undefined;
  isLoading: boolean;
}

const CATEGORIES = [
  { code: 'telecom', name: 'Telekommunikasiya', icon: Cable, color: '#e74c3c' },
  { code: 'water', name: 'Su təchizatı', icon: Droplets, color: '#1abc9c' },
  { code: 'gas', name: 'Qaz təchizatı', icon: Flame, color: '#f39c12' },
  { code: 'electricity', name: 'Elektrik', icon: Zap, color: '#e67e22' },
];

export default function Sidebar({ filters, setFilters, operators, stats, isLoading }: SidebarProps) {
  const [layersOpen, setLayersOpen] = useState(true);
  const [operatorsOpen, setOperatorsOpen] = useState(true);
  const [categoriesOpen, setCategoriesOpen] = useState(true);

  const toggleOperator = (code: string) => {
    setFilters(prev => ({
      ...prev,
      operators: prev.operators.includes(code)
        ? prev.operators.filter(o => o !== code)
        : [...prev.operators, code],
    }));
  };

  const toggleCategory = (code: string) => {
    setFilters(prev => ({
      ...prev,
      categories: prev.categories.includes(code)
        ? prev.categories.filter(c => c !== code)
        : [...prev.categories, code],
    }));
  };

  const clearFilters = () => {
    setFilters({
      operators: [],
      categories: [],
      showInfrastructure: true,
      showBuildings: true,
    });
  };

  const hasFilters = filters.operators.length > 0 || filters.categories.length > 0;

  return (
    <aside className="w-80 bg-white border-r border-gray-200 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-lg">
            <MapIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Urban Lens</h1>
            <p className="text-xs text-blue-100">Şəhər İnfrastrukturu</p>
          </div>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 bg-white rounded-lg shadow-sm">
              <div className="text-xl font-bold text-blue-600">{stats.total_infrastructure}</div>
              <div className="text-xs text-gray-500">İnfrastruktur</div>
            </div>
            <div className="p-2 bg-white rounded-lg shadow-sm">
              <div className="text-xl font-bold text-green-600">{stats.total_buildings}</div>
              <div className="text-xs text-gray-500">Bina</div>
            </div>
            <div className="p-2 bg-white rounded-lg shadow-sm">
              <div className="text-xl font-bold text-purple-600">{stats.total_streets}</div>
              <div className="text-xs text-gray-500">Küçə</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex-1 overflow-y-auto">
        {/* Clear filters button */}
        {hasFilters && (
          <div className="p-3 border-b border-gray-200">
            <button
              onClick={clearFilters}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
            >
              <X className="w-4 h-4" />
              Filterləri təmizlə
            </button>
          </div>
        )}

        {/* Layers Section */}
        <div className="border-b border-gray-200">
          <button
            onClick={() => setLayersOpen(!layersOpen)}
            className="flex items-center justify-between w-full p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-gray-500" />
              <span className="font-medium text-gray-700">Qatlar</span>
            </div>
            {layersOpen ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {layersOpen && (
            <div className="px-4 pb-4 space-y-2">
              <label className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.showInfrastructure}
                  onChange={(e) => setFilters(prev => ({ ...prev, showInfrastructure: e.target.checked }))}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <Cable className="w-5 h-5 text-orange-500" />
                <span className="text-sm text-gray-700">İnfrastruktur</span>
              </label>
              
              <label className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.showBuildings}
                  onChange={(e) => setFilters(prev => ({ ...prev, showBuildings: e.target.checked }))}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <Building2 className="w-5 h-5 text-blue-500" />
                <span className="text-sm text-gray-700">Binalar</span>
              </label>
            </div>
          )}
        </div>

        {/* Categories Section */}
        <div className="border-b border-gray-200">
          <button
            onClick={() => setCategoriesOpen(!categoriesOpen)}
            className="flex items-center justify-between w-full p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-500" />
              <span className="font-medium text-gray-700">Kateqoriyalar</span>
            </div>
            {categoriesOpen ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {categoriesOpen && (
            <div className="px-4 pb-4 space-y-2">
              {CATEGORIES.map((cat) => {
                const Icon = cat.icon;
                const isSelected = filters.categories.includes(cat.code);
                return (
                  <label
                    key={cat.code}
                    className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleCategory(cat.code)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: cat.color }}
                    />
                    <Icon className="w-4 h-4" style={{ color: cat.color }} />
                    <span className="text-sm text-gray-700">{cat.name}</span>
                  </label>
                );
              })}
            </div>
          )}
        </div>

        {/* Operators Section */}
        <div className="border-b border-gray-200">
          <button
            onClick={() => setOperatorsOpen(!operatorsOpen)}
            className="flex items-center justify-between w-full p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-gray-500" />
              <span className="font-medium text-gray-700">Operatorlar</span>
            </div>
            {operatorsOpen ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {operatorsOpen && (
            <div className="px-4 pb-4 space-y-2 max-h-64 overflow-y-auto">
              {isLoading ? (
                <div className="text-sm text-gray-500 p-2">Yüklənir...</div>
              ) : (
                operators.map((op) => {
                  const isSelected = filters.operators.includes(op.code);
                  return (
                    <label
                      key={op.code}
                      className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                        isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleOperator(op.code)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: op.color }}
                      />
                      <div className="min-w-0">
                        <div className="text-sm text-gray-700 truncate">{op.name_az || op.name}</div>
                        <div className="text-xs text-gray-400">{op.category}</div>
                      </div>
                    </label>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-500 text-center">
          <p>National Space Hackathon 2024</p>
          <p className="mt-1">Azercosmos</p>
        </div>
      </div>
    </aside>
  );
}
