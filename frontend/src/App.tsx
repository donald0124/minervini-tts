import { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { FilterBar } from './components/FilterBar';
import { StockTable } from './components/StockTable';
import type { APIResponse } from './types/schema';
import { Loader2, AlertCircle } from 'lucide-react';

// 開發環境下，請將此處指向您的後端路徑，或將 results.json 複製到 public/
// 在 Codespaces 中，如果前後端分開跑，可能需要指向 '/backend/output/results.json' 
// 或者我們假設您已經把 results.json 放到 frontend/public 了
// const DATA_URL = 'backend/output/results.json'; 
// const DATA_URL = `${import.meta.env.BASE_URL}results.json`;

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const DATA_URL = `${API_BASE}/data/results.json`;

function App() {
    const [data, setData] = useState<APIResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [search, setSearch] = useState("");
    const [showPassOnly, setShowPassOnly] = useState(false);

    useEffect(() => {
        fetch(DATA_URL)
            .then(res => {
                if (!res.ok) throw new Error("無法讀取資料");
                return res.json();
            })
            .then(setData)
            .catch(err => {
                console.error(err);
                setError("無法載入選股資料，請確認後端是否已執行完畢。");
            })
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="flex flex-col items-center gap-2 text-gray-500">
                    <Loader2 className="animate-spin" size={32} />
                    <span className="text-sm">正在載入數據...</span>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="bg-white p-8 rounded-lg shadow-sm border border-red-100 flex flex-col items-center gap-4 max-w-md text-center">
                    <div className="p-3 bg-red-50 rounded-full text-red-500">
                        <AlertCircle size={32} />
                    </div>
                    <h2 className="text-lg font-bold text-gray-900">載入失敗</h2>
                    <p className="text-sm text-gray-600">{error}</p>
                    <button 
                        onClick={() => window.location.reload()}
                        className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm hover:bg-gray-800 transition-colors"
                    >
                        重新整理
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 pb-12">
            <Header metadata={data.metadata} />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
                <FilterBar 
                    search={search}
                    onSearchChange={setSearch}
                    showPassOnly={showPassOnly}
                    onTogglePassOnly={setShowPassOnly}
                />

                <StockTable 
                    data={data.data}
                    showPassOnly={showPassOnly}
                    globalFilter={search}
                />
            </main>
        </div>
    );
}

export default App;