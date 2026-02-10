import type { Metadata } from '../types/schema';
import { Clock, Sliders } from 'lucide-react';

interface Props {
    metadata: Metadata;
}

export function Header({ metadata }: Props) {
    return (
        <header className="bg-white border-b border-gray-200 py-4 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">MTTS Dashboard</h1>
                    <p className="text-sm text-gray-500 mt-1">Minervini Trend Template Screener</p>
                </div>

                <div className="flex flex-col items-end gap-2 text-sm">
                    <div className="flex items-center text-gray-600 gap-1.5 bg-gray-50 px-3 py-1.5 rounded-md">
                        <Clock size={16} />
                        <span>更新: {new Date(metadata.timestamp).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Sliders size={14} className="text-gray-400" />
                        <span className="text-xs text-gray-500 font-mono">
                            RS&gt;{metadata.config.rs_threshold} | Vol&gt;{metadata.config.min_volume}
                        </span>
                    </div>
                </div>
            </div>
        </header>
    );
}