import axios from 'axios';
import { API_BASE_URL } from '../config';

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const MarketService = {
    /**
     * 글로벌 탄소 가격 동향 (EU-ETS vs K-ETS)
     */
    async getMarketTrends(period: string = '1y', signal?: AbortSignal) {
        const response = await api.get(`/api/v1/sim/dashboard/market-trends`, {
            params: { period },
            signal
        });
        return response.data;
    },

    
};

export const AiService = {
    /**
     * AI 전략 생성
     */
    async generateStrategy(companyId: number, market: string, currentPrice: number) {
        const response = await api.post(`/api/v1/ai/strategy`, {
            companyId,
            market,
            currentPrice
        });
        return response.data;
    },

    /**
     * AI 채팅 (스트리밍)
     */
    async chatStream(
        params: {
            message: string;
            history?: Array<{ role: string; text: string }>;
            companyName?: string;
            companyKey?: string;
            reportScope?: string;
            reportYear?: number | null;
        },
        onChunk: (chunk: string) => void
    ) {
        const response = await fetch(`${API_BASE_URL}/api/v1/ai/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        });

        if (!response.body) {
            throw new Error('ReadableStream not supported');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            onChunk(chunk);
        }
    }
};
