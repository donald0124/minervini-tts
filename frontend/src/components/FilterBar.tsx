import { Search } from 'lucide-react';

interface Props {
    search: string;
    onSearchChange: (val: string) => void;
    showPassOnly: boolean;
    onTogglePassOnly: (val: boolean) => void;
}

export function FilterBar({ search, onSearchChange, showPassOnly, onTogglePassOnly }: Props) {
    return (
        <div className="flex flex-col sm:flex-row gap-4 mb-6 justify-between items-center">
            <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input 
                    type="text" 
                    placeholder="搜尋代號或名稱..." 
                    value={search}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
            </div>

            <label className="flex items-center gap-2 cursor-pointer bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm hover:bg-gray-50">
                <input 
                    type="checkbox" 
                    checked={showPassOnly}
                    onChange={(e) => onTogglePassOnly(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">只顯示合格股票 (PASS)</span>
            </label>
        </div>
    );
}