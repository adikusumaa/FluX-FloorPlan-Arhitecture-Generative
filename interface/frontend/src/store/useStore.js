import { create } from 'zustand';

const useStore = create((set) => ({
  userText: '',
  coordinates: { lat: -6.2, lng: 106.8 },
  loading: false,
  error: null,
  results: null,
  setUserText: (text) => set({ userText: text }),
  setCoordinates: (coords) => set({ coordinates: coords }),
  setLoading: (loading) => set({ loading }),
  setResults: (data) => set({ results: data, loading: false, error: null }),
  setError: (msg) => set({ error: msg, loading: false }),
  reset: () => set({ results: null, error: null }),
}));

export default useStore;