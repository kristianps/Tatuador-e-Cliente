const backendLocal = "http://127.0.0.1:8000";
const backendAlternativo = "http://localhost:8000";
const backendProdução = "https://backend-two-gray-28.vercel.app";

const enderecoApi =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.MODE === "production" ? backendProdução : backendLocal) ||
  backendAlternativo;

export { enderecoApi };
export default enderecoApi;
