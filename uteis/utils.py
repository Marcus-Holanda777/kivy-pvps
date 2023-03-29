import requests
import re
from modelos import Produto, db, and_, _asdict
from models.controle import db as dbb

def download_pvps(dep: int):
    key_validate = {
        'emb', 'salvo', 'codigo', 'quantidade',
        'verificado', 'vencimento', 'endereco', 'tipos',
        'zona', 'descricao', 'estoque'
    }

    def is_kay_validate(val):
        return set(val.keys()) == key_validate

    get_dep = [
        row.val()
        for row in dbb.child('pvps').child(str(dep)).get().each()
        if row.val() is not None and is_kay_validate(row.val())
    ]

    return get_dep


def id_return(texto: str) -> int:
    return int(texto.split(':')[1].strip())


def is_data(texto: str):
    comp = re.compile(
        r'''^
           (0[1-9]|[12][0-9]|3[01])
           /
           (0[1-9]|1[012])
           /
           [12][0-9]{3}
           $
        ''',
        re.I | re.VERBOSE
    )

    if comp.search(texto):
        return True
    else:
        return False


def is_connect(timeout: float = 5.0) -> bool:
    url = "http://www.google.com"
    try:
        __ = requests.get(url, timeout=timeout)
        return True
    except Exception:
        return False


def sincronizar_dados(deposito: str) -> int:
    try:
        rst = (
            db.query(
                Produto
            )
            .filter(
                and_(
                    Produto.verificado == True,
                    Produto.salvo == False
                )
            )
        ).all()

        if len(rst) == 0:
            # NADA PRA ATUALIZAR
            return 202

        rst = {row.produto_id - 1: _asdict(row, True) for row in rst}

        dbb.child("pvps").child(deposito).update(
            rst
        )

    except:
        # UMA EXCESAO
        return 303
    else:
        # TUDO CERTO
        return 200
