import { clsx } from 'clsx';

interface Props {
    status: "PASS" | "FAIL";
}

export function StatusBadge({ status }: Props) {
    return (
        <span className={clsx(
            "px-2 py-1 rounded-full text-xs font-medium",
            status === "PASS" 
                ? "bg-green-100 text-green-800 border border-green-200"
                : "bg-red-50 text-red-600 border border-red-100"
        )}>
            {status}
        </span>
    );
}