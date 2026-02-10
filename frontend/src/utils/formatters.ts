export function formatVolume(val: number): string {
    // 將股數轉為張數 (1張 = 1000股)
    const lots = Math.round(val / 1000);
    
    // 格式化千分位
    return new Intl.NumberFormat('en-US').format(lots);
}

export function formatPrice(val: number): string {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 2
    }).format(val);
}