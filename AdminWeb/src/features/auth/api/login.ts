import { api } from '../../../lib/axios';

export type LoginPayload = {
    email: string;
    password: string;
};

export type LoginResponse = {
    token: string;
    user: {
        user_id: number;
        user_name: string;
        email: string;
    };
};

// API sends POSTs using axios
export async function login(payload: LoginPayload): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/api/auth/login', payload);
    return data;
}
