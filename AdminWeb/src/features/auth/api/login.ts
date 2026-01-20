import axios from 'axios';

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
    withCredentials: true,
});

export type LoginPayload = {
    ucid: string;
    password: string;
};

export type LoginResponse = {
    token: string;
    user: {
        ucid: string;
        FirstName: string;
        LastName: string;
    };
};

// API sends POSTs using axios
export async function login(payload: LoginPayload): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/auth/login', payload);
    return data;
}
