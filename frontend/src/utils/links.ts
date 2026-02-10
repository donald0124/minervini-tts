export function getTradingViewUrl(ticker: string): string {
    const code = ticker.split('.')[0];
    let market = 'TWSE'; 

    if (ticker.includes('.TWO')) {
        market = 'TPEX'; 
    }

    return `https://www.tradingview.com/chart/?symbol=${market}:${code}`;
}