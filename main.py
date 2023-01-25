from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.clock import mainthread

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.list import (TwoLineIconListItem, IconLeftWidget,
                             ThreeLineRightIconListItem)

from kivymd.uix.snackbar import Snackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDFillRoundFlatIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField

from modelos import db, Produto, func, and_, _asdict
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from datetime import datetime
from threading import Thread
from time import sleep
import re

from uteis.utils import is_connect, is_data

from models.controle import db as dbb
from models.autenticar import criar_conta, autenticar_conta

# Window.size = (360, 548)  # config TELA


class CustomLista(ThreeLineRightIconListItem):
    text = StringProperty()
    secondary_text = StringProperty()
    tertiary_text = StringProperty()

    def app_editar(self):
        app = MDApp.get_running_app()
        app.root.current_screen.manager.transition.direction = 'left'
        app.root.current = 'appdeditver'

        screen = app.root.current_screen

        id = int(self.text.split(':')[1].strip())
        prod = db.query(Produto).filter(Produto.produto_id == id).scalar()

        screen.ids.id_prod.text = f'ID: {str(prod.produto_id)}'
        screen.ids.endereco.text = prod.endereco
        screen.ids.nome.text = prod.descricao
        screen.ids.emb.text = "1"

        if app.app_atual == 'applistazonaver':
            screen.ids.quantidade.text = str(prod.quantidade)
            screen.ids.validade.text = parse(
                prod.vencimento).strftime("%d/%m/%Y")
        else:
            screen.ids.quantidade.text = ''
            screen.ids.validade.text = ''


class TextDate(MDTextField):
    pat = re.compile(r'(\d{2})(\d{4})')

    def insert_text(self, substring, from_undo=False):
        if not substring.isnumeric():
            substring = ""

        s = self.text + substring

        if len(s) == 6:
            self.text = (
                parse(self.pat.sub(r"01/\1/\2", s), dayfirst=True) +
                relativedelta(day=31)
            ).strftime("%d/%m/%Y")

            self.do_cursor_movement("cursor_end")
            substring = ""
        elif len(s) > 10:
            self.text = s[:10]
            substring = ""

        return super().insert_text(substring, from_undo)


class BtnEditar(MDFillRoundFlatIconButton):
    ...


class BtnAdicionar(MDFillRoundFlatIconButton):
    ...


class Content(MDBoxLayout):
    def add_new_validade(self, id):
        self.app = MDApp.get_running_app()

        text_error = "ERRO"
        bg_color_error = get_color_from_hex('#E91E63')
        text_ok = "SALVO"
        bg_color_ok = get_color_from_hex('#276880')

        self.snack = Snackbar(
            snackbar_x="10dp",
            snackbar_y="10dp",
            size_hint_x=(
                Window.width - (dp(10) * 2)
            ) / Window.width
        )

        is_campo = all(
            [
                self.ids.quantidade.text != "",
                self.ids.validade.text != ""
            ]
        )

        if is_campo and is_connect() and is_data(self.ids.validade.text):
            idd = int(id.split(":")[1].strip())
            prod = (
                db.query(Produto)
                .filter(Produto.produto_id == idd)
            ).first()

            # TODO -> Verificar se data ja existe
            is_val = db.query(Produto).filter(
                and_(Produto.codigo == prod.codigo,
                     Produto.vencimento == self.ids.validade.text)
            ).scalar()

            if not is_val:
                inseridos = (
                    db.query(func.sum(Produto.quantidade))
                    .filter(Produto.codigo == prod.codigo)
                ).scalar() + int(self.ids.quantidade.text)

                if inseridos <= prod.estoque:

                    new_prod = Produto()
                    new_prod.codigo = prod.codigo
                    new_prod.endereco = prod.endereco
                    new_prod.descricao = prod.descricao
                    new_prod.estoque = prod.estoque
                    new_prod.quantidade = int(self.ids.quantidade.text)
                    new_prod.tipos = prod.tipos
                    new_prod.vencimento = parse(
                        self.ids.validade.text, dayfirst=True).strftime('%d/%m/%Y')
                    new_prod.verificado = True
                    new_prod.zona = prod.zona

                    dados = _asdict(new_prod)

                    # TODO -> Gravar os dados
                    db.add(new_prod)
                    db.commit()

                    # TODO -> Gravar no banco online
                    dbb.child("pvps").child(self.app.deposito).child(
                        self.app.total).update(dados)

                    self.app.total += 1

                    self.ids.quantidade.text = ""
                    self.ids.validade.text = ""

                    self.snack.text = text_ok
                    self.snack.bg_color = bg_color_ok
                    self.snack.open()
                else:
                    self.snack.text = f"Qtd inserida {inseridos} > {prod.estoque}"
                    self.snack.bg_color = bg_color_error
                    self.snack.open()

            else:
                self.snack.text = "VALIDADE JA EXISTE"
                self.snack.bg_color = bg_color_error
                self.snack.open()

        else:
            self.snack.text = text_error
            self.snack.bg_color = bg_color_error
            self.snack.open()


class AppdEditVer(MDScreen):
    max_length = 7

    def on_pre_enter(self, *args):
        Window.bind(on_keyboard=self.hook_keyboard)
        self.add_btn_edit()

    def add_btn_novo(self, *args):
        self.btn = BtnAdicionar()
        self.ids.layout.add_widget(self.btn)
        self.btn.bind(on_release=self.add_validade)

        try:
            self.ids.layout.remove_widget(self.btn_edit)
        except AttributeError:
            pass

    def add_btn_edit(self, *args):
        self.app = MDApp.get_running_app()

        self.btn_edit = BtnEditar()
        self.ids.layout.add_widget(self.btn_edit)
        self.btn_edit.bind(on_release=self.app.atualizar)

        try:
            self.ids.layout.remove_widget(self.btn)
        except AttributeError:
            pass

    def remove_btn_edit(self, *args):
        try:
            self.ids.layout.remove_widget(self.btn_edit)
        except Exception:
            pass

    def add_validade(self, *args):
        self.dialog = MDDialog(
            title="ADD VALIDADE:",
            type="custom",
            content_cls=Content(),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    on_press=lambda x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    on_press=lambda x: self.dialog.content_cls.add_new_validade(
                        self.ids.id_prod.text
                    )
                ),
            ],
        )

        self.dialog.open()

    def calcula_total(self):

        if self.ids.quantidade.text.strip() == "" or len(self.ids.quantidade.text) > self.max_length:
            self.ids.total.text = "0"
        elif self.ids.emb.text == "" or self.ids.emb.text == "0":
            self.ids.total.text = "0"
        else:
            self.ids.total.text = (
                str(
                    int(self.ids.quantidade.text) *
                    int(self.ids.emb.text)
                )
            )

    def hook_keyboard(self, window, key, *args):
        self.app = MDApp.get_running_app()

        if key == 27:
            self.app.altera_screen(
                self.app.zona, self.app.tipo, self.app.pesquisa, self.app.search, "right")

            return True

    def on_pre_leave(self, *args):
        self.app = MDApp.get_running_app()
        self.app.altera_screen(
            self.app.zona, self.app.tipo, self.app.pesquisa, self.app.search, "right")

        Window.unbind(on_keyboard=self.hook_keyboard)
        self.remove_btn_edit()


class AppCardZona(MDScreen):
    def on_pre_enter(self, *args):
        Window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *args):
        if key == 27:
            MDApp.get_running_app().root.current_screen.manager.transition.direction = 'right'
            MDApp.get_running_app().root.current = 'applogin'
            return True

    def on_pre_leave(self, *args):
        Window.unbind(on_keyboard=self.hook_keyboard)


class AppLista(MDScreen):
    def on_pre_enter(self, *args):
        Window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *args):
        if key == 27:
            MDApp.get_running_app().root.current_screen.manager.transition.direction = 'right'
            MDApp.get_running_app().root.current = 'appcardzona'
            return True

    def on_pre_leave(self, *args):
        Window.unbind(on_keyboard=self.hook_keyboard)


class AppListaNaoVerificados(MDScreen):
    def on_pre_enter(self, *args):
        Window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *args):
        app = MDApp.get_running_app()

        if key == 27:
            app.root.current_screen.manager.transition.direction = 'right'
            app.root.current = 'applistazona'
            app.cria_lista_zona()
            return True

    def on_pre_leave(self, *args):
        Window.unbind(on_keyboard=self.hook_keyboard)


class AppListaVerificados(MDScreen):
    def on_pre_enter(self, *args):
        Window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *args):
        app = MDApp.get_running_app()

        if key == 27:
            app.root.current_screen.manager.transition.direction = 'right'
            app.root.current = 'applistazona'
            app.cria_lista_zona(True)
            return True

    def on_pre_leave(self, *args):
        Window.unbind(on_keyboard=self.hook_keyboard)


class AppLogin(MDScreen):
    txt_matricula = ObjectProperty(None)
    txt_login = ObjectProperty(None)
    icon_login = ObjectProperty(None)

    estado = BooleanProperty(False)
    deposito = None

    def on_leave(self, *args):
        self.txt_matricula.text = ''
        self.txt_login.text = ''
        self.txt_login.password = True
        self.icon_login.icon = 'eye-off'

    def start_second_thread(self):
        t = Thread(target=self.autenticar)
        t.start()

    def autenticar(self):
        self.update_conecta(True)
        self.deposito, self.title, self.text = autenticar_conta()

        if self.deposito:
            self.update_conecta(False)
            self.alterar()
        else:
            sleep(2.0)
            self.update_conecta(False)
            self.alterar()

    @mainthread
    def alterar(self):
        app = MDApp.get_running_app()

        if self.deposito:
            app.atualizar_base()
        else:
            app.dialog = MDDialog(
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        text_color=app.theme_cls.primary_color,
                        on_press=lambda x: app.dialog.dismiss()
                    )
                ]
            )

            app.dialog.title = self.title
            app.dialog.text = self.text
            app.dialog.open()

    @mainthread
    def update_conecta(self, estado: bool):
        self.estado = estado


class AppCriar(MDScreen):
    txt_matricula = ObjectProperty(None)
    txt_email = ObjectProperty(None)
    txt_login = ObjectProperty(None)
    icon_login = ObjectProperty(None)

    def on_leave(self, *args):
        self.txt_matricula.text = ''
        self.txt_email.text = ''
        self.txt_login.text = ''
        self.txt_login.password = True
        self.icon_login.icon = 'eye-off'

    def on_pre_enter(self, *args):
        Window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *args):
        if key == 27:
            MDApp.get_running_app().root.current_screen.manager.transition.direction = 'right'
            MDApp.get_running_app().root.current = 'applogin'
            return True

    def on_pre_leave(self, *args):
        Window.unbind(on_keyboard=self.hook_keyboard)


screen_manager = MDScreenManager()
screen_manager.add_widget(AppLogin(name='applogin'))
screen_manager.add_widget(AppCriar(name='appcriar'))
screen_manager.add_widget(AppCardZona(name='appcardzona'))
screen_manager.add_widget(AppLista(name='applistazona'))
screen_manager.add_widget(AppListaNaoVerificados(name='applistazonanaover'))
screen_manager.add_widget(AppListaVerificados(name='applistazonaver'))
screen_manager.add_widget(AppdEditVer(name='appdeditver'))


class MainApp(MDApp):

    def build(self):
        self.deposito = None
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Purple"
        self.theme_cls.material_style = "M3"

        return Builder.load_file("Main.kv")

    def criar_cadastro(self):
        criar_conta()

    def mensagem(self):
        self.diag = MDDialog(
            title="ERRO",
            text="Favor verificar internet, senha ou login !",
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_press=lambda x: self.diag.dismiss()
                )
            ]
        )

        self.diag.open()

    def sel_deposito(self):
        def set_item(text_item):
            self.root.current_screen.ids.drop_item.set_item(text_item)
            self.root.current_screen.ids.drop_item.text = text_item
            self.menu.dismiss()

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"Deposito {i}",
                "height": dp(56),
                "on_release": lambda x=f"Deposito {i}": set_item(x),
            } for i in range(1, 10)
        ]

        self.menu = MDDropdownMenu(
            caller=self.root.current_screen.ids.drop_item,
            items=menu_items,
            position="center",
            max_height=dp(115),
            width_mult=4,
        )

        # self.menu.bind()
        self.menu.open()

    def atualizar_base(self):

        if is_connect():

            # trazendo o deposito do APPLOGIN
            self.deposito = self.root.current_screen.deposito

            db.query(Produto).delete()
            db.bulk_insert_mappings(Produto, dbb.child(
                "pvps").child(self.deposito).get().val())
            db.commit()

            self.verificado = (
                db.query(Produto)
                .filter(Produto.verificado == True)
            ).count()

            self.nao_verificado = (
                db.query(Produto)
                .filter(Produto.verificado == False)
            ).count()

            self.root.current_screen.manager.transition.direction = 'left'
            self.root.current = 'appcardzona'
            self.total_verificado()
            self.root.current_screen.ids.lbl_deposito.text = f"DEPOSITO - {int(self.deposito):02d}"
            self.root.current_screen.ids.btn_naover.text = (
                f"NAO VERIFICADOS\n"
                f"{int(self.nao_verificado): 02d}"
            )
            self.root.current_screen.ids.btn_ver.text = (
                f"    VERIFICADOS\n"
                f"{int(self.verificado): 02d}"
            )

        else:
            self.mensagem()

    def total_verificado(self):
        self.total = db.query(Produto).count()

        self.ver_precentual = round((self.verificado / self.total) * 100, 2)
        self.root.current_screen.ids.lbl_progess.text = f"{self.ver_precentual} %"

        self.root.current_screen.ids.progresstotal.value = (
            self.verificado / self.total) * 100

    def filtra_zona(self, zona, tipo, pesquisa="", search=False):
        self.pesquisa = pesquisa
        self.search = search
        self.root.current_screen.ids.rv.data = []

        # TODO: Retorna dados por Zona
        if search:
            rst = (
                db.query(Produto)
                .filter(and_(Produto.zona == zona, Produto.tipos == tipo,
                             Produto.verificado == self.flag_ver,
                             Produto.descricao.like(f"%{pesquisa}%")))
            ).all()

        else:
            rst = (
                db.query(Produto)
                .filter(and_(Produto.zona == zona, Produto.tipos == tipo,
                             Produto.verificado == self.flag_ver))
            ).all()

        for row in rst:
            dados = {
                'viewclass': 'CustomLista',
                'text': f'ID: {row.produto_id:>10}',
                'secondary_text': f'ED: {row.endereco}',
                'tertiary_text': f'DS: {row.descricao}',
                'callback': lambda x: x,
            }

            self.zona = zona
            self.tipo = tipo

            self.root.current_screen.ids.rv.data.append(dados)

    def altera_screen(self, zona, tipo, pesquisa="", search=False, lado='left'):
        tipo = tipo.split('-')[0].strip()

        if self.flag_ver:
            self.app_atual = 'applistazonaver'
        else:
            self.app_atual = 'applistazonanaover'

        self.root.current_screen.manager.transition.direction = lado
        self.root.current = self.app_atual
        self.filtra_zona(zona, tipo, pesquisa, search)

    def cria_lista_zona(self, flag_ver=False):
        self.flag_ver = flag_ver

        # limpando a lista
        self.root.current_screen.ids.md_list.clear_widgets()

        # define o icone se med ou nmed
        def icones(x): return 'pill-multiple' if x.value == 0 else 'pill-off'

        # TODO: Retorna dados por Zona
        rst = (
            db.query(Produto.zona, Produto.tipos, func.Count().label('total'))
            .filter(Produto.verificado == flag_ver)
            .group_by(Produto.zona, Produto.tipos)
        ).all()

        for row in rst:
            it = TwoLineIconListItem(
                text=f"{row.zona}",
                secondary_text=f'{row.tipos.name:>10} - {row.total:>5}',
                on_release=lambda x: self.altera_screen(
                    x.text, x.secondary_text)
            )

            it.add_widget(
                IconLeftWidget(
                    icon=icones(row.tipos)
                )
            )
            self.root.current_screen.ids.md_list.add_widget(it)

    def on_save(self, instance, value, date_range):
        screen = self.root.current_screen

        dt_fim = value + relativedelta(day=31)
        screen.ids.validade.text = dt_fim.strftime("%d/%m/%Y")

    def on_cancel(self, instance, value):
        Snackbar(
            text=f"VENC CANCELADO",
            snackbar_x="10dp",
            snackbar_y="10dp",
            bg_color=get_color_from_hex('#E91E63'),
            size_hint_x=(
                Window.width - (dp(10) * 2)
            ) / Window.width
        ).open()

    def show_data(self):
        ano_atual = datetime.now().year

        data = MDDatePicker(title="VENC", title_input='VENC',
                            min_year=ano_atual, max_year=ano_atual + 6)
        data.bind(on_save=self.on_save, on_cancel=self.on_cancel)
        data.open()

    def atualizar(self, *args):
        screen = self.root.current_screen

        id = int(screen.ids.id_prod.text.split(':')[1].strip())
        qtd = screen.ids.quantidade.text
        validade = screen.ids.validade.text

        msg_erro = "ERRO"

        if qtd != '' and validade != '':

            try:
                if not is_data(validade):
                    msg_erro = f"FORMATO DE DATA ERRADA {validade}"
                    raise ValueError

                datetime.strptime(validade, "%d/%m/%Y")

                prod = (
                    db.query(Produto)
                    .filter(Produto.produto_id == id)
                ).first()

                # TODO -> VERIFICAR ESTOQUE NA HORA DE INSERIR NA BASE
                if self.app_atual == 'applistazonanaover':

                    inseridos = (
                        db.query(func.sum(Produto.quantidade))
                        .filter(Produto.codigo == prod.codigo)
                    ).scalar() + int(qtd)

                    # TODO -> Verificar se data ja existe
                    is_val = db.query(Produto).filter(
                        and_(Produto.codigo == prod.codigo,
                             Produto.vencimento == validade)
                    ).scalar()

                    if is_val:
                        msg_erro = "VALIDADE JA EXISTE"
                        raise ValueError

                else:
                    inseridos = (
                        db.query(func.sum(Produto.quantidade))
                        .filter(Produto.codigo == prod.codigo)
                    ).scalar() - prod.quantidade

                    inseridos += int(qtd)

                if inseridos > prod.estoque:
                    msg_erro = f"Qtd inserida {inseridos} > {prod.estoque}"
                    raise ValueError

                prod.quantidade = int(qtd)
                prod.vencimento = parse(validade, dayfirst=True)

                prod.verificado = True
                db.commit()

                dbb.child("pvps").child(self.deposito).child(id - 1).update(
                    {
                        "quantidade": int(qtd),
                        "vencimento": validade,
                        "verificado": True
                    }
                )

            except:
                texto = msg_erro
                cor = get_color_from_hex('#E91E63')
            else:
                texto = 'SALVO'
                cor = get_color_from_hex('#276880')

                if self.app_atual == 'applistazonanaover':
                    # REINICIAR CAMPOS
                    screen.ids.quantidade.text = ''
                    screen.ids.validade.text = ''
                    screen.add_btn_novo()

        else:
            texto = msg_erro
            cor = get_color_from_hex('#E91E63')

        Snackbar(
            text=texto,
            snackbar_x="10dp",
            snackbar_y="10dp",
            bg_color=cor,
            size_hint_x=(
                Window.width - (dp(10) * 2)
            ) / Window.width
        ).open()


if __name__ == '__main__':
    MainApp().run()
