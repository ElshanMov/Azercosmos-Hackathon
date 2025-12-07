import { useState, useEffect } from 'react';

interface Operator {
  id: string;
  name: string;
  name_short?: string;
  category: string;
}

interface Stats {
  operator: string;
  infrastructure_count: number;
  building_count: number;
  last_import: string | null;
}

interface ImportResult {
  total: number;
  imported: number;
  errors: number;
  message: string;
  first_error?: string;
  detected_type?: string;
}

interface OperatorPortalProps {
  onBack: () => void;
}

const CATEGORY_ICONS: Record<string, string> = {
  water: '💧',
  building: '🏛️',
  telecom: '📡',
};

const CATEGORY_COLORS: Record<string, string> = {
  water: '#06b6d4',
  building: '#8b5cf6',
  telecom: '#6366f1',
};

export default function OperatorPortal({ onBack }: OperatorPortalProps) {
  const [operators, setOperators] = useState<Operator[]>([]);
  const [currentOperator, setCurrentOperator] = useState<Operator | null>(null);
  const [password, setPassword] = useState('');
  const [selectedOperatorId, setSelectedOperatorId] = useState('');
  const [loginError, setLoginError] = useState('');
  const [stats, setStats] = useState<Stats | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    fetch('/api/operator/list')
      .then(res => res.json())
      .then(data => Array.isArray(data) && setOperators(data))
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (currentOperator) {
      fetch(`/api/operator/stats/${currentOperator.id}`)
        .then(res => res.json())
        .then(setStats)
        .catch(console.error);
    }
  }, [currentOperator, importResult]);

  const handleLogin = async () => {
    setLoginError('');
    try {
      const res = await fetch('/api/operator/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operator_id: selectedOperatorId, password })
      });
      const data = await res.json();
      data.success ? setCurrentOperator(data.operator) : setLoginError(data.message);
    } catch {
      setLoginError('Bağlantı xətası');
    }
  };

  const handleLogout = () => {
    setCurrentOperator(null);
    setStats(null);
    setPassword('');
    setSelectedOperatorId('');
    setImportResult(null);
  };

  const handleFileSelect = (file: File | null) => {
    if (file && (file.name.endsWith('.geojson') || file.name.endsWith('.json'))) {
      setSelectedFile(file);
      setImportResult(null);
    } else if (file) {
      setImportResult({ total: 0, imported: 0, errors: 1, message: 'Yalnız GeoJSON faylları qəbul edilir' });
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleImport = async () => {
    if (!selectedFile || !currentOperator) return;
    
    setImporting(true);
    setImportResult(null);
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const res = await fetch(`/api/operator/import/${currentOperator.id}`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setImportResult(data);
      if (data.imported > 0) {
        // Refresh stats
        const statsRes = await fetch(`/api/operator/stats/${currentOperator.id}`);
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch {
      setImportResult({ total: 0, imported: 0, errors: 1, message: 'Import xətası baş verdi' });
    } finally {
      setImporting(false);
      setSelectedFile(null);
    }
  };

  // Login Screen
  if (!currentOperator) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-8 text-white text-center">
            <div className="text-4xl mb-2">🏢</div>
            <h1 className="text-2xl font-bold">Operator Portal</h1>
            <p className="text-indigo-100 mt-1">Məkan Data İdarəetmə Sistemi</p>
          </div>
          
          <div className="p-8">
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Qurum seçin</label>
              <select
                value={selectedOperatorId}
                onChange={(e) => setSelectedOperatorId(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white text-sm"
              >
                <option value="">-- Qurum seçin --</option>
                {operators.map(op => (
                  <option key={op.id} value={op.id}>
                    {CATEGORY_ICONS[op.category]} {op.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Şifrə</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Şifrənizi daxil edin"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              />
            </div>
            
            {loginError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{loginError}</div>
            )}
            
            <button
              onClick={handleLogin}
              disabled={!selectedOperatorId || !password}
              className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 transition-all"
            >
              Daxil ol
            </button>
            
            <button onClick={onBack} className="w-full mt-4 py-2 text-gray-600 hover:text-gray-900 text-sm">
              ← Xəritəyə qayıt
            </button>

            {/* Login info */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 font-medium mb-2">Demo giriş məlumatları:</p>
              <div className="space-y-1 text-xs text-gray-600">
                <p>🏛️ Şəhərsalma: <code className="bg-gray-200 px-1 rounded">shahersalma2025</code></p>
                <p>💧 Su Təchizatı: <code className="bg-gray-200 px-1 rounded">sutechizati2025</code></p>
                <p>📡 Aztelekom: <code className="bg-gray-200 px-1 rounded">aztelekom2025</code></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const categoryColor = CATEGORY_COLORS[currentOperator.category] || '#6b7280';
  
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style={{ backgroundColor: `${categoryColor}20` }}>
              {CATEGORY_ICONS[currentOperator.category]}
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">{currentOperator.name_short || currentOperator.name}</h1>
              <p className="text-sm text-gray-500">Operator Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={onBack} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm">🗺️ Xəritə</button>
            <button onClick={handleLogout} className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg text-sm">Çıxış</button>
          </div>
        </div>
      </header>
      
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6 border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">İnfrastruktur</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stats?.infrastructure_count || 0}</p>
              </div>
              <div className="w-12 h-12 bg-cyan-100 rounded-xl flex items-center justify-center text-2xl">🔧</div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-6 border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Binalar</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stats?.building_count || 0}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center text-2xl">🏢</div>
            </div>
          </div>
        </div>
        
        {/* Import Section */}
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="p-6 border-b bg-gradient-to-r from-indigo-50 to-purple-50">
            <h2 className="text-lg font-semibold text-gray-900">GeoJSON Import</h2>
            <p className="text-sm text-gray-500 mt-1">Məkan datasını sistemə yükləyin</p>
          </div>
          
          <div className="p-6">
            {/* Drag & Drop Zone */}
            <div 
              className={`border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer ${
                dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <input
                id="file-input"
                type="file"
                onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
                accept=".geojson,.json"
                className="hidden"
              />
              
              {selectedFile ? (
                <div>
                  <div className="text-4xl mb-3">📄</div>
                  <p className="text-gray-900 font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500 mt-1">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div>
                  <div className="text-4xl mb-3">📁</div>
                  <p className="text-gray-600">GeoJSON faylını bura sürükləyin</p>
                  <p className="text-sm text-gray-400 mt-1">və ya klikləyib seçin</p>
                </div>
              )}
            </div>
            
            {/* Info */}
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>ℹ️ Qeyd:</strong> Sistem yüklənən datanın tipini (bina və ya infrastruktur) avtomatik müəyyən edəcək.
              </p>
            </div>
            
            {/* Import Button */}
            <button
              onClick={handleImport}
              disabled={!selectedFile || importing}
              className="w-full mt-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {importing ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Import edilir...
                </>
              ) : '📤 Import et'}
            </button>
            
            {/* Import Result */}
            {importResult && (
              <div className={`mt-4 p-4 rounded-lg ${
                importResult.errors === 0 && importResult.imported > 0 ? 'bg-green-50 border border-green-200' : 
                importResult.imported > 0 ? 'bg-yellow-50 border border-yellow-200' :
                'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-start gap-3">
                  <div className="text-2xl">
                    {importResult.errors === 0 && importResult.imported > 0 ? '✅' : 
                     importResult.imported > 0 ? '⚠️' : '❌'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{importResult.message}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Cəmi: {importResult.total} | Uğurlu: {importResult.imported} | Xəta: {importResult.errors}
                      {importResult.detected_type && (
                        <span className="ml-2 px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">
                          {importResult.detected_type === 'infrastructure' ? '🔧 İnfrastruktur' : '🏢 Bina'}
                        </span>
                      )}
                    </p>
                    {importResult.first_error && (
                      <div className="mt-3 p-3 bg-white rounded border border-red-200">
                        <p className="text-xs font-medium text-red-700 mb-1">İlk xəta:</p>
                        <p className="text-xs text-red-600 font-mono break-all">{importResult.first_error}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}