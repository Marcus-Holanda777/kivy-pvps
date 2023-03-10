from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Enum, inspect, func, Boolean, and_, or_
from sqlalchemy.ext.declarative import declarative_base, as_declarative
from sqlalchemy.orm import sessionmaker
import enum

Base = declarative_base()
engine = create_engine('sqlite:///Produtos.db')


def _asdict(obj, flag=False):
    dados = {c.key: getattr(obj, c.key)
             for c in inspect(obj).mapper.column_attrs}
    dados.pop('produto_id')
    dados['tipos'] = obj.tipos.name

    if flag:
        dados['salvo'] = True

    return dados


Session = sessionmaker(bind=engine)
db = Session()


class Tipos(enum.Enum):
    MED = 0
    NMED = 1


class Produto(Base):
    __tablename__ = 'produtos'

    produto_id = Column(Integer(), primary_key=True)
    codigo = Column(Integer(), index=True, nullable=False)
    descricao = Column(String())
    emb = Column(Integer(), nullable=False)
    endereco = Column(String(), nullable=False)
    estoque = Column(Integer(), nullable=False, default=0)
    quantidade = Column(Integer(), nullable=False, default=0)
    salvo = Column(Boolean(), nullable=False, default=False)
    tipos = Column(Enum(Tipos), index=True, nullable=False)
    vencimento = Column(String(), default=None)
    verificado = Column(Boolean(), nullable=False, default=False)
    zona = Column(String(), nullable=False)

    def __repr__(self) -> str:
        return f'Produtos(tipos={self.tipos})'


Base.metadata.create_all(bind=engine)
