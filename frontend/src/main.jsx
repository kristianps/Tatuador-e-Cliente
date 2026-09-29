import { createRoot } from "react-dom/client";

import Aplicacao from "./Aplicacao.jsx";
import "./estilos.css";

// Monta a aplicação React no elemento raiz da página HTML.
createRoot(document.getElementById("raiz")).render(<Aplicacao />);
