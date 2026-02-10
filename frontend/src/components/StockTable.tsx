import { useState, useMemo, Fragment } from 'react';
import { 
    useReactTable, 
    getCoreRowModel, 
    getSortedRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    getExpandedRowModel, // 新增
    flexRender,
} from '@tanstack/react-table';

import type { ColumnDef, SortingState, ExpandedState } from '@tanstack/react-table';
import type { StockData } from '../types/schema';

import { StatusBadge } from './StatusBadge';
import { formatVolume, formatPrice } from '../utils/formatters';
import { getTradingViewUrl } from '../utils/links';
import { ExternalLink, ArrowUpDown, ChevronRight, ChevronDown, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import { clsx } from 'clsx';

interface Props {
    data: StockData[];
    showPassOnly: boolean;
    globalFilter: string;
}

// === 子組件：展開後的詳細資訊 ===
function ExpandedRow({ row }: { row: StockData }) {
    const { details, indicators, price } = row;
    
    // 定義條件的中文描述
    const criteriaMap: Record<string, string> = {
        c1_trend_stack: "C1: 均線多頭排列 (價格 > 150 > 200)",
        c2_long_term: "C2: 長期均線向上 (150 > 200)",
        c3_ma200_slope: "C3: 200MA 處於上升趨勢",
        c4_mid_term: "C4: 中期趨勢確認 (50 > 150 & 200)",
        c5_momentum: "C5: 短期動能強勁 (價格 > 50MA)",
        c6_support: "C6: 脫離底部 (高於 52週低點 30%)",
        c7_resistance: "C7: 消化賣壓 (距 52週高點 25% 內)",
        c8_rs_strength: "C8: 相對強度優異 (RS Rating >= 70)"
    };

    // 計算乖離率 Helper
    const getDiff = (target: number) => {
        if (!target) return "N/A";
        const diff = ((price - target) / target) * 100;
        return (
            <span className={diff > 0 ? "text-red-600" : "text-green-600"}>
                ({diff > 0 ? "+" : ""}{diff.toFixed(1)}%)
            </span>
        );
    };

    return (
        <div className="p-4 bg-gray-50 border-t border-b border-gray-200 grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            {/* 左側：篩選條件檢核表 */}
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <h4 className="font-bold text-gray-700 mb-3 border-b pb-2">篩選條件細項 ({row.match_count})</h4>
                <div className="space-y-2">
                    {Object.entries(criteriaMap).map(([key, label]) => (
                        <div key={key} className="flex items-start gap-2">
                            {details[key] ? (
                                <CheckCircle2 size={16} className="text-green-500 mt-0.5 shrink-0" />
                            ) : (
                                <XCircle size={16} className="text-red-400 mt-0.5 shrink-0" />
                            )}
                            <span className={clsx(details[key] ? "text-gray-700" : "text-gray-400")}>
                                {label}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 右側：關鍵價位數據 */}
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <h4 className="font-bold text-gray-700 mb-3 border-b pb-2">關鍵技術指標</h4>
                <div className="grid grid-cols-2 gap-y-3 gap-x-4">
                    <div className="col-span-2 flex justify-between items-center bg-gray-50 p-2 rounded">
                        <span className="text-gray-500">目前股價</span>
                        <span className="font-bold text-lg text-gray-900">{formatPrice(price)}</span>
                    </div>
                    
                    <div className="flex flex-col">
                        <span className="text-xs text-gray-500">50日均線 (季線)</span>
                        <div className="flex justify-between items-baseline">
                            <span className="font-mono">{formatPrice(indicators.SMA_50)}</span>
                            <span className="text-xs">{getDiff(indicators.SMA_50)}</span>
                        </div>
                    </div>

                    <div className="flex flex-col">
                        <span className="text-xs text-gray-500">150日均線</span>
                        <div className="flex justify-between items-baseline">
                            <span className="font-mono">{formatPrice(indicators.SMA_150)}</span>
                            <span className="text-xs">{getDiff(indicators.SMA_150)}</span>
                        </div>
                    </div>

                    <div className="flex flex-col">
                        <span className="text-xs text-gray-500">200日均線 (年線)</span>
                        <div className="flex justify-between items-baseline">
                            <span className="font-mono">{formatPrice(indicators.SMA_200)}</span>
                            <span className="text-xs">{getDiff(indicators.SMA_200)}</span>
                        </div>
                    </div>
                    
                    <div className="flex flex-col">
                        <span className="text-xs text-gray-500">200MA 斜率 (前月比)</span>
                        <div className="flex justify-between items-baseline">
                           <span className={clsx("font-mono font-medium", indicators.SMA_200 > indicators.SMA_200_Prev ? "text-red-600" : "text-green-600")}>
                                {indicators.SMA_200 > indicators.SMA_200_Prev ? "↗ 上升" : "↘ 下降"}
                           </span>
                           <span className="text-xs text-gray-400">{formatPrice(indicators.SMA_200_Prev)}</span>
                        </div>
                    </div>

                    <div className="col-span-2 border-t pt-2 mt-1 grid grid-cols-2 gap-4">
                        <div className="flex flex-col">
                            <span className="text-xs text-gray-500">52週最高</span>
                            <div className="flex justify-between items-baseline">
                                <span className="font-mono">{formatPrice(indicators.High_52W)}</span>
                                <span className="text-xs text-green-600">{row.dist_high_pct}</span>
                            </div>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xs text-gray-500">52週最低</span>
                            <div className="flex justify-between items-baseline">
                                <span className="font-mono">{formatPrice(indicators.Low_52W)}</span>
                                <span className="text-xs text-red-600">+{row.dist_low_pct}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// === 主表格組件 ===
export function StockTable({ data, showPassOnly, globalFilter }: Props) {
    const [sorting, setSorting] = useState<SortingState>([
        { id: 'status', desc: false },
        { id: 'rs_rating', desc: true }
    ]);
    const [expanded, setExpanded] = useState<ExpandedState>({}); // 新增展開狀態

    // 分頁設定：預設 20 筆
    const [pagination, setPagination] = useState({
        pageIndex: 0,
        pageSize: 20,
    });

    const filteredData = useMemo(() => {
        let res = data;
        if (showPassOnly) {
            res = res.filter(d => d.status === "PASS");
        }
        return res;
    }, [data, showPassOnly]);

    const columns = useMemo<ColumnDef<StockData>[]>(() => [
        // 1. 展開按鈕欄位
        {
            id: 'expander',
            header: () => null,
            cell: ({ row }) => {
                return row.getCanExpand() ? (
                    <button
                        onClick={row.getToggleExpandedHandler()}
                        className="p-1 hover:bg-gray-100 rounded text-gray-500 transition-colors"
                    >
                        {row.getIsExpanded() ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </button>
                ) : null;
            },
        },
        // 2. 原有欄位
        {
            accessorKey: 'ticker',
            header: '股票',
            cell: ({ row }) => {
                const tickerRaw = row.original.ticker;
                const isOTC = tickerRaw.includes('.TWO');
                // 乾淨的代號：移除所有後綴
                const cleanCode = tickerRaw.replace('.TWO', '').replace('.TW', '');
                
                return (
                    <a 
                        href={getTradingViewUrl(tickerRaw)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group flex flex-col"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1 font-bold text-gray-900 group-hover:text-blue-600">
                                {cleanCode}
                                <ExternalLink size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                            <span className={clsx(
                                "text-[10px] px-1 rounded border",
                                isOTC 
                                    ? "bg-emerald-50 text-emerald-600 border-emerald-200" // 上櫃顏色
                                    : "bg-blue-50 text-blue-600 border-blue-200"         // 上市顏色
                            )}>
                                {isOTC ? '櫃' : '市'}
                            </span>
                            
                        </div>
                        <span className="text-xs text-gray-500 mt-0.5">{row.original.name}</span>
                    </a>
                )
            }
        },
        {
            accessorKey: 'price',
            header: ({ column }) => (
                <div 
                    className="flex items-center justify-end gap-1 cursor-pointer"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                >
                    價格 <ArrowUpDown size={12} />
                </div>
            ),
            cell: info => <div className="text-right font-mono">{formatPrice(info.getValue() as number)}</div>
        },
        {
            accessorKey: 'rs_rating',
            header: ({ column }) => (
                <div 
                    className="flex items-center gap-1 cursor-pointer"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                >
                    RS <ArrowUpDown size={12} />
                </div>
            ),
            cell: info => {
                const val = info.getValue() as number;
                return (
                    <span className={clsx("font-mono font-medium", val >= 90 ? "text-amber-600 font-bold" : "text-gray-600")}>
                        {val}
                    </span>
                );
            }
        },
        {
            accessorKey: 'vol_avg',
            header: ({ column }) => (
                <div 
                    className="flex items-center gap-1 cursor-pointer hover:text-gray-900"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                >
                    20日均量(張) <ArrowUpDown size={12} />
                </div>
            ),
            cell: info => <span className="text-gray-600 text-sm font-mono">{formatVolume(info.getValue() as number)}</span>
        },
        {
            accessorKey: 'status',
            header: ({ column }) => (
                <div 
                    className="flex items-center gap-1 cursor-pointer hover:text-gray-900"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                >
                    狀態 <ArrowUpDown size={12} />
                </div>
            ),
            cell: info => <StatusBadge status={info.getValue() as any} />
        },
        {
            accessorKey: 'match_count',
            header: ({ column }) => (
                <div 
                    className="flex items-center gap-1 cursor-pointer hover:text-gray-900"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                >
                    符合 <ArrowUpDown size={12} />
                </div>
            ),
            cell: ({ row }) => {
                const count = row.original.match_count; // e.g., "8/8"
                const isLiquidityFail = row.original.status === "FAIL" && count === "8/8";
                
                return (
                    <div className="flex items-center gap-2">
                        <span className={clsx(
                            "text-xs font-mono px-1.5 py-0.5 rounded",
                            isLiquidityFail ? "bg-amber-100 text-amber-800 font-bold" : "bg-gray-100 text-gray-700"
                        )}>
                            {count}
                        </span>
                        {isLiquidityFail && (
                            <div className="flex items-center text-[10px] text-amber-600 bg-amber-50 px-1 rounded border border-amber-100">
                                <AlertTriangle size={10} className="mr-0.5" />
                                量縮
                            </div>
                        )}
                    </div>
                );
            },
            meta: { className: "hidden md:table-cell" }
        },
    ], []);


    const table = useReactTable({
        data: filteredData,
        columns,
        state: {
            sorting,
            globalFilter,
            expanded,
            pagination,
        },
        onSortingChange: setSorting,
        onExpandedChange: setExpanded,
        onPaginationChange: setPagination,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getExpandedRowModel: getExpandedRowModel(),
        getRowCanExpand: () => true,
        globalFilterFn: (row, _columnId, filterValue) => {
            const search = filterValue.toLowerCase();
            return row.original.ticker.toLowerCase().includes(search) || 
                   row.original.name.toLowerCase().includes(search);
        }
    });

    return (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                        {table.getHeaderGroups().map(headerGroup => (
                            <tr key={headerGroup.id}>
                                {/* 展開欄位通常很窄，給定固定寬度 */}
                                {headerGroup.headers.map(header => (
                                    <th key={header.id} className={clsx("px-4 py-3 font-medium", (header.column.columnDef.meta as any)?.className, header.id === 'expander' && 'w-10')}>
                                        {flexRender(header.column.columnDef.header, header.getContext())}
                                    </th>
                                ))}
                            </tr>
                        ))}
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {table.getRowModel().rows.map(row => (
                            <Fragment key={row.id}>
                                {/* 主資料列 */}
                                <tr 
                                    className={clsx("hover:bg-gray-50 transition-colors cursor-pointer", row.getIsExpanded() && "bg-gray-50")}
                                    onClick={row.getToggleExpandedHandler()} // 點擊整行也可展開
                                >
                                    {row.getVisibleCells().map(cell => (
                                        <td key={cell.id} className={clsx("px-4 py-3", (cell.column.columnDef.meta as any)?.className)}>
                                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                        </td>
                                    ))}
                                </tr>
                                
                                {/* 展開內容列 */}
                                {row.getIsExpanded() && (
                                    <tr>
                                        <td colSpan={row.getVisibleCells().length} className="p-0 border-none">
                                            <ExpandedRow row={row.original} />
                                        </td>
                                    </tr>
                                )}
                            </Fragment>
                        ))}
                    </tbody>
                </table>
            </div>
            
            {/* Pagination Controls */}
            <div className="px-4 py-3 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>
                        顯示 {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} - {Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, filteredData.length)} 共 {filteredData.length} 筆
                    </span>
                    
                    <div className="flex items-center gap-2">
                        <span>每頁顯示:</span>
                        <select
                            value={table.getState().pagination.pageSize}
                            onChange={e => {
                                table.setPageSize(Number(e.target.value))
                            }}
                            className="border border-gray-300 rounded px-2 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            {[10, 20, 50, 100].map(pageSize => (
                                <option key={pageSize} value={pageSize}>
                                    {pageSize}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="flex gap-2">
                    <button 
                        onClick={() => table.previousPage()} 
                        disabled={!table.getCanPreviousPage()}
                        className="px-3 py-1 border rounded text-xs disabled:opacity-50 hover:bg-gray-50 disabled:cursor-not-allowed"
                    >
                        上一頁
                    </button>
                    <button 
                        onClick={() => table.nextPage()} 
                        disabled={!table.getCanNextPage()}
                        className="px-3 py-1 border rounded text-xs disabled:opacity-50 hover:bg-gray-50 disabled:cursor-not-allowed"
                    >
                        下一頁
                    </button>
                </div>
            </div>
        </div>
    );
}