import { create } from 'zustand';

const useStore = create((set) => ({
  userText: '',
  weights: [0.25, 0.25, 0.25, 0.25],
  coordinates: { lat: -6.2, lng: 106.8 },
  loading: false,
  results: null,
  parsedData: null,
  statusMessage: '',
  error: null,
  setUserText: (text) => set({ userText: text }),
  setWeights: (weights) => set({ weights }),
  setCoordinates: (coords) => set({ coordinates: coords }),
  setLoading: (loading) => set({ loading }),
  setResults: (data, parsed) => set({ results: data, parsedData: parsed }),
  setError: (error) => set({ error }),
  setStatusMessage: (msg) => set({ statusMessage: msg }),
  reset: () => set({ userText: '', results: null, parsedData: null, statusMessage: '' }),
}));

export default useStore;