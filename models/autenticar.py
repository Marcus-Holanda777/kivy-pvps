from models.controle import auth, db
from requests.exceptions import HTTPError
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from uteis.utils import is_connect
from kivymd.app import MDApp


def is_usuario(matricula: str) -> bool:
    rst = db.child("users").child(matricula).get()

    if rst.val():
        return True
    else:
        return False


def is_dados(deposito: str) -> bool:
    rst = db.child("pvps").child(deposito).get()

    if rst.val():
        return True
    else:
        return False


def autenticar_conta() -> None:
    self = MDApp.get_running_app()
    screen = self.root.current_screen

    matricula = screen.ids.matricula.text
    senha = screen.ids.login.text

    is_campos = all(
        [
            matricula.strip() != "",
            senha.strip() != "",
        ]
    )

    title = "ERRO"
    text = "Senha ou login errado"

    try:
        if not is_connect():
            title = "ERRO INTERNET"
            text = "Sem conexao com a internet !"
            raise HTTPError

        if not is_campos:
            title = "ERRO CAMPOS"
            text = "Verificar todos os campos !"
            raise HTTPError

        if is_usuario(matricula):
            dados = db.child("users").child(matricula).get().val()
            deposito = dados["dep"]
            email = dados["email"]
        else:
            title = "ERRO CADASTRO"
            text = "Usuario nao possui cadastro !"
            raise HTTPError

        if not is_dados(deposito):
            title = "ERRO BASE"
            text = f"Deposito {deposito} nao possui base de dados !"
            raise HTTPError

        usr = auth.sign_in_with_email_and_password(
            email,
            senha
        )

        token = usr['idToken']
        return (deposito, title, text)

    except HTTPError:
        return (None, title, text)


def criar_conta() -> None:
    self = MDApp.get_running_app()
    screen = self.root.current_screen

    matricula = screen.ids.matricula.text
    email = screen.ids.email.text
    senha = screen.ids.login.text
    deposito = screen.ids.drop_item.text.split(" ")[1].strip()

    is_campos = all(
        [
            matricula.strip() != "",
            email.strip() != "",
            senha.strip() != "",
        ]
    )

    title = "ERRO"
    text = "Nao foi possivel cadastrar !"

    self.dialog = MDDialog(
        buttons=[
            MDFlatButton(
                text="OK",
                theme_text_color="Custom",
                text_color=self.theme_cls.primary_color,
                on_press=lambda x: self.dialog.dismiss()
            )
        ]
    )

    try:
        if not is_connect:
            title = "ERRO INTERNET"
            text = "Sem conexao com a internet !"
            raise HTTPError

        if not is_campos:
            title = "ERRO CAMPOS"
            text = "Verificar todos os campos !"
            raise HTTPError

        if is_usuario(matricula):
            title = "ERRO CADASTRO"
            text = "Usuario ja possui cadastro !"
            raise HTTPError

        usr = auth.create_user_with_email_and_password(
            email,
            senha
        )

        token = usr['idToken']

        if token:
            db.child("users").update(
                {
                    matricula: {
                        "email": email,
                        "dep": deposito,
                    }
                }, token
            )

            self.dialog.title = "CADASTRO"
            self.dialog.text = "Cadastrado com Sucesso !"
            self.dialog.open()

    except HTTPError:
        self.dialog.title = title
        self.dialog.text = text
        self.dialog.open()
