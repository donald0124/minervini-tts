import { useState, useMemo } from 'react';
import { 
    useReactTable, 
    getCoreRowModel, 
    getSortedRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    flexRender,
} from '@tanstack/react-table';

// 修改處 1：將型別拆出來並加上 type
import type { ColumnDef, SortingState } from '@tanstack/react-table';

// 修改處 2：加上 type
import type { StockData } from '../types/schema';

import { StatusBadge } from './StatusBadge';
import { formatVolume, formatPrice } from '../utils/formatters';
import { getTradingViewUrl } from '../utils/links';
import { ExternalLink, ArrowUpDown } from 'lucide-react';
import { clsx } from 'clsx';


interface Props {
    data: StockData[];
    showPassOnly: boolean;
    globalFilter: string;
}

export function StockTable({ data, showPassOnly, globalFilter }: Props) {
    const [sorting, setSorting] = useState<SortingState>([
        { id: 'status', desc: false }, // PASS first
        { id: 'rs_rating', desc: true } // Then High RS
    ]);

    // Filter Logic
    const filteredData = useMemo(() => {
        let res = data;
        if (showPassOnly) {
            res = res.filter(d => d.status === "PASS");
        }
        return res;
    }, [data, showPassOnly]);

    const columns = useMemo<ColumnDef<StockData>[]>(() => [
        {
            accessorKey: 'ticker',
            header: '股票',
            cell: ({ row }) => (
                <a 
                    href={getTradingViewUrl(row.original.ticker)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex flex-col"
                >
                    <div className="flex items-center gap-1 font-bold text-blue-600 group-hover:underline">
                        {row.original.ticker.replace('.TW', '').replace('.TWO', '')}
                        <ExternalLink size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <span className="text-xs text-gray-500">{row.original.name}</span>
                </a>
            )
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
            header: '均量',
            cell: info => <span className="text-gray-500 text-sm">{formatVolume(info.getValue() as number)}</span>
        },
        {
            accessorKey: 'status',
            header: '狀態',
            cell: info => <StatusBadge status={info.getValue() as any} />
        },
        {
            accessorKey: 'match_count',
            header: '符合',
            cell: info => <span className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded">{info.getValue() as string}</span>,
            meta: { className: "hidden md:table-cell" } // Mobile hide
        },
        {
            accessorKey: 'fail_reason',
            header: '備註',
            cell: info => <span className="text-xs text-red-500 truncate max-w-[120px] block">{info.getValue() as string}</span>,
            meta: { className: "hidden md:table-cell" }
        }
    ], []);

    const table = useReactTable({
        data: filteredData,
        columns,
        state: {
            sorting,
            globalFilter,
        },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        globalFilterFn: (row, columnId, filterValue) => {
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
                                {headerGroup.headers.map(header => (
                                    <th key={header.id} className={clsx("px-4 py-3 font-medium", (header.column.columnDef.meta as any)?.className)}>
                                        {flexRender(header.column.columnDef.header, header.getContext())}
                                    </th>
                                ))}
                            </tr>
                        ))}
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {table.getRowModel().rows.map(row => (
                            <tr key={row.id} className="hover:bg-gray-50 transition-colors">
                                {row.getVisibleCells().map(cell => (
                                    <td key={cell.id} className={clsx("px-4 py-3", (cell.column.columnDef.meta as any)?.className)}>
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
                <div className="text-xs text-gray-500">
                    顯示 {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} - {Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, filteredData.length)} 共 {filteredData.length} 筆
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={() => table.previousPage()} 
                        disabled={!table.getCanPreviousPage()}
                        className="px-3 py-1 border rounded text-xs disabled:opacity-50"
                    >
                        上一頁
                    </button>
                    <button 
                        onClick={() => table.nextPage()} 
                        disabled={!table.getCanNextPage()}
                        className="px-3 py-1 border rounded text-xs disabled:opacity-50"
                    >
                        下一頁
                    </button>
                </div>
            </div>
        </div>
    );
}