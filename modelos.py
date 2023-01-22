from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Enum, inspect, func, Boolean, and_
from sqlalchemy.ext.declarative import declarative_base, as_declarative
from sqlalchemy.orm import sessionmaker
import enum

Base = declarative_base()
engine = create_engine('sqlite:///Produtos.db')


@as_declarative()
class Base:
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}


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
    endereco = Column(String(), nullable=False)
    estoque = Column(Integer(), nullable=False, default=0)
    quantidade = Column(Integer(), nullable=False, default=0)
    tipos = Column(Enum(Tipos), index=True, nullable=False)
    vencimento = Column(String(), default=None)
    verificado = Column(Boolean(), nullable=False, default=False)
    zona = Column(String(), nullable=False)

    def __repr__(self) -> str:
        return f'Produtos(tipos={self.tipos})'


Base.metadata.create_all(bind=engine)
