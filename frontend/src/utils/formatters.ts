export function formatVolume(val: number): string {
    if (val >= 1000000) {
        return (val / 1000000).toFixed(1) + 'M';
    }
    if (val >= 1000) {
        return (val / 1000).toFixed(1) + 'K';
    }
    return val.toString();
}

export function formatPrice(val: number): string {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 2
    }).format(val);
}