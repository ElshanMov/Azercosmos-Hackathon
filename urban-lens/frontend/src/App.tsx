import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Map from './components/Map';
import Sidebar from './components/Sidebar';
import FeaturePanel from './components/FeaturePanel';
import { useStats, useOperators } from './hooks/useApi';
import type { FilterState } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const [filters, setFilters] = useState<FilterState>({
    operators: [],
    categories: [],
    showInfrastructure: true,
    showBuildings: true,
  });

  const [selectedFeature, setSelectedFeature] = useState<GeoJSON.Feature | null>(null);

  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: operators = [], isLoading: operatorsLoading } = useOperators();

  const handleFeatureClick = (feature: GeoJSON.Feature) => {
    setSelectedFeature(feature);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-100">
      {/* Sidebar */}
      <Sidebar
        filters={filters}
        setFilters={setFilters}
        operators={operators}
        stats={stats}
        isLoading={operatorsLoading || statsLoading}
      />

      {/* Map Container */}
      <div className="flex-1 relative">
        <Map
          filters={filters}
          onFeatureClick={handleFeatureClick}
        />

        {/* Feature Panel */}
        <FeaturePanel
          feature={selectedFeature}
          onClose={() => setSelectedFeature(null)}
        />

        {/* Legend */}
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-3 z-[500]">
          <h4 className="text-xs font-semibold text-gray-600 mb-2">Əfsanə</h4>
          <div className="space-y-1.5 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-red-500 rounded"></div>
              <span>Telekommunikasiya</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-teal-500 rounded"></div>
              <span>Su təchizatı</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-yellow-500 rounded"></div>
              <span>Qaz</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-1 bg-orange-500 rounded"></div>
              <span>Elektrik</span>
            </div>
            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-200">
              <div className="w-3 h-3 bg-blue-400 border border-gray-400 rounded-sm"></div>
              <span>Binalar</span>
            </div>
          </div>
        </div>

        {/* Loading indicator */}
        {(statsLoading || operatorsLoading) && (
          <div className="absolute top-4 right-20 bg-blue-600 text-white px-3 py-1.5 rounded-lg shadow-lg text-sm z-[500]">
            Yüklənir...
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
