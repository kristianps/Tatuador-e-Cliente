from typing import Optional

# Tipos de imagem aceitos nos anexos. Só fotos comuns, em base64, no formato data URL.
TIPOS_IMAGEM = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")

# Tamanho máximo do anexo em caracteres. A tela já reduz a foto antes de enviar,
# então uma imagem normal fica bem abaixo disso; o limite barra arquivos enormes.
TAMANHO_MAXIMO_IMAGEM = 2_000_000


# Usada pelos esquemas que recebem imagem: recusa o que não for PNG, JPEG ou WebP em base64.
def conferir_imagem(valor: Optional[str]) -> Optional[str]:
    if valor is not None and not valor.startswith(TIPOS_IMAGEM):
        raise ValueError("A imagem precisa ser PNG, JPEG ou WebP.")
    return valor
