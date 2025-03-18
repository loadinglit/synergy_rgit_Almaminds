import { create } from 'zustand';

interface User {
  id: string;
  email: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => set({ user: null, isAuthenticated: false })
}));

interface VideoState {
  videos: any[];
  loading: boolean;
  setVideos: (videos: any[]) => void;
  setLoading: (loading: boolean) => void;
}

export const useVideoStore = create<VideoState>((set) => ({
  videos: [],
  loading: false,
  setVideos: (videos) => set({ videos }),
  setLoading: (loading) => set({ loading })
}));