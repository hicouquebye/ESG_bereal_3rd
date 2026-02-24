import { API_BASE_URL } from '../config';

export interface SignupData {
    email: string;
    password: string;
    company_name: string;
}

export interface LoginData {
    email: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export interface UserResponse {
    id: number;
    email: string;
    company_name: string;
    created_at: string;
}

const parseApiError = async (response: Response, fallback: string): Promise<string> => {
    try {
        const error = await response.json();
        return error.detail || fallback;
    } catch {
        return fallback;
    }
};

const FETCH_TIMEOUT_MS = 10000;

const fetchWithTimeout = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
        return await fetch(input, { ...init, signal: controller.signal });
    } finally {
        clearTimeout(timeoutId);
    }
};

export const signup = async (data: SignupData): Promise<UserResponse> => {
    let response: Response;
    try {
        response = await fetchWithTimeout(`${API_BASE_URL}/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
    } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') {
            throw new Error(`요청 시간이 초과되었습니다. 백엔드 상태를 확인해주세요. (${API_BASE_URL})`);
        }
        throw new Error(`백엔드 서버에 연결할 수 없습니다. (${API_BASE_URL})`);
    }

    if (!response.ok) {
        throw new Error(await parseApiError(response, '회원가입에 실패했습니다.'));
    }

    return response.json();
};

export const login = async (data: LoginData): Promise<TokenResponse> => {
    let response: Response;
    try {
        response = await fetchWithTimeout(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
    } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') {
            throw new Error(`요청 시간이 초과되었습니다. 백엔드 상태를 확인해주세요. (${API_BASE_URL})`);
        }
        throw new Error(`백엔드 서버에 연결할 수 없습니다. (${API_BASE_URL})`);
    }

    if (!response.ok) {
        throw new Error(await parseApiError(response, '로그인에 실패했습니다.'));
    }

    return response.json();
};

export const getCurrentUser = async (token: string): Promise<UserResponse> => {
    let response: Response;
    try {
        response = await fetchWithTimeout(`${API_BASE_URL}/auth/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
    } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') {
            throw new Error(`요청 시간이 초과되었습니다. 백엔드 상태를 확인해주세요. (${API_BASE_URL})`);
        }
        throw new Error(`백엔드 서버에 연결할 수 없습니다. (${API_BASE_URL})`);
    }

    if (!response.ok) {
        throw new Error(await parseApiError(response, '사용자 정보를 가져오지 못했습니다.'));
    }

    return response.json();
};

export const saveToken = (token: string): void => {
    localStorage.setItem('auth_token', token);
};

export const getToken = (): string | null => {
    return localStorage.getItem('auth_token');
};

export const removeToken = (): void => {
    localStorage.removeItem('auth_token');
};

export const isAuthenticated = (): boolean => {
    return getToken() !== null;
};
