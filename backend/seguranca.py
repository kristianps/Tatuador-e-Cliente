import hashlib
import hmac
import secrets

import configuracao

# Formato salvo no banco: algoritmo$iterações$sal$hash.
# Guardar as iterações junto permite aumentar o custo no futuro sem invalidar as senhas antigas.
ALGORITMO = "pbkdf2_sha256"
ITERACOES = 300_000

# Chave usada como sal fixo nas versões antigas do sistema. Fica aqui só para conferir
# senhas criadas antes da mudança; a conta passa para o formato novo no próximo login.
_SEGREDO_PADRAO_ANTIGO = "pereiratatto-secreto-demo"


def _pbkdf2(senha: str, sal: bytes, iteracoes: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, iteracoes).hex()


# Cada senha ganha um sal aleatório próprio: duas pessoas com a mesma senha ficam com hashes diferentes.
def gerar_hash_senha(senha: str) -> str:
    sal = secrets.token_bytes(16)
    return f"{ALGORITMO}${ITERACOES}${sal.hex()}${_pbkdf2(senha, sal, ITERACOES)}"


# Hash antigo: só o hexadecimal, sem o prefixo do algoritmo.
def _eh_formato_antigo(senha_hash: str) -> bool:
    return "$" not in senha_hash


def verificar_senha(senha: str, senha_hash: str) -> bool:
    if not senha_hash:
        return False

    if _eh_formato_antigo(senha_hash):
        # O sal antigo era a chave do JWT; confere com a chave atual e com o valor padrão de antes.
        segredos = {configuracao.JWT_SECRET_KEY, _SEGREDO_PADRAO_ANTIGO} - {""}
        return any(
            hmac.compare_digest(_pbkdf2(senha, segredo.encode("utf-8"), 100_000), senha_hash)
            for segredo in segredos
        )

    try:
        algoritmo, iteracoes, sal_hex, hash_hex = senha_hash.split("$")
        if algoritmo != ALGORITMO:
            return False
        calculado = _pbkdf2(senha, bytes.fromhex(sal_hex), int(iteracoes))
    except ValueError:
        return False

    # compare_digest leva o mesmo tempo acerte ou erre, para não dar pistas a quem tenta adivinhar.
    return hmac.compare_digest(calculado, hash_hex)


# Diz se o hash salvo deve ser refeito no formato atual (formato antigo ou menos iterações).
def precisa_atualizar(senha_hash: str) -> bool:
    if _eh_formato_antigo(senha_hash):
        return True
    partes = senha_hash.split("$")
    return len(partes) != 4 or partes[0] != ALGORITMO or partes[1] != str(ITERACOES)
