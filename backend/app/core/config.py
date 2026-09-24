"""Configuração da aplicação, lida do ambiente (.env)."""
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CHAVE_DE_EXEMPLO = "troque-esta-chave-em-producao"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Aplicação ────────────────────────────────────────────────────
    APP_NOME: str = "SmartCondo API"
    APP_VERSAO: str = "0.1.0"
    DEBUG: bool = False

    # ── Banco de dados (documentação, seção 19.5: PostgreSQL) ────────
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://smartcondo:smartcondo@localhost:5432/smartcondo",
        description="URL de conexão do PostgreSQL.",
    )

    # ── Autenticação ─────────────────────────────────────────────────
    # Em produção esta chave vem do ambiente; nunca deve ficar no código.
    SECRET_KEY: str = Field(default=CHAVE_DE_EXEMPLO, min_length=16)
    ALGORITMO_JWT: str = "HS256"
    ACCESS_TOKEN_EXPIRA_MIN: int = 60 * 8

    # Custo do bcrypt. 12 e o padrao seguro; os testes baixam para 4 para
    # nao gastar segundos por hash.
    BCRYPT_ROUNDS: int = Field(default=12, ge=4, le=16)

    # Validade do código de confirmação de cadastro e de recuperação de
    # senha (documentação, seção 12: "Cadastro" e "Esqueci minha senha").
    CODIGO_VERIFICACAO_EXPIRA_MIN: int = 15
    # Frequência máxima de códigos por pessoa e finalidade. Sem limite,
    # qualquer um dispara "esqueci minha senha" com o e-mail de outra
    # pessoa sem parar — cada SMS é pago —, e cada código novo traria mais
    # tentativas para adivinhar.
    CODIGO_INTERVALO_S: int = Field(default=60, ge=0, le=3600)
    CODIGO_MAX_POR_HORA: int = Field(default=5, ge=1, le=100)

    # Quantas senhas erradas seguidas antes de trancar a conta, e por
    # quanto tempo. O bloqueio é temporário de propósito: permanente,
    # bastaria errar a senha de alguém para deixá-lo de fora.
    MAX_TENTATIVAS_LOGIN: int = Field(default=5, ge=3, le=20)
    BLOQUEIO_LOGIN_MIN: int = Field(default=15, ge=1, le=1440)

    # ── Envio de e-mail ──────────────────────────────────────────────
    # Sem SMTP_HOST o código não é enviado: fica só no log, que serve
    # para desenvolvimento. Em produção isso trava o cadastro — o
    # morador espera um código que nunca chega —, por isso a aplicação
    # avisa em voz alta ao subir sem SMTP com DEBUG desligado.
    SMTP_HOST: str = ""
    SMTP_PORTA: int = Field(default=587, ge=1, le=65535)
    SMTP_USUARIO: str = ""
    SMTP_SENHA: str = ""
    SMTP_TLS: bool = True
    SMTP_REMETENTE: str = "SmartCondo <nao-responda@smartcondo.com>"
    # Um servidor SMTP lento não pode segurar a requisição do cadastro.
    SMTP_TIMEOUT_S: int = Field(default=10, ge=1, le=60)

    @property
    def email_configurado(self) -> bool:
        return bool(self.SMTP_HOST)

    # ── Envio de SMS ─────────────────────────────────────────────────
    # Pelo Twilio (twilio.com): SMS_CONTA é o Account SID, SMS_TOKEN o
    # Auth Token e SMS_REMETENTE o número comprado lá, no formato
    # +5567999990000. Sem os três, a tela não oferece SMS e o código vai
    # por e-mail. O serviço é pago por mensagem.
    SMS_CONTA: str = ""
    SMS_TOKEN: str = ""
    SMS_REMETENTE: str = ""
    SMS_TIMEOUT_S: int = Field(default=10, ge=1, le=60)

    @property
    def sms_configurado(self) -> bool:
        return bool(self.SMS_CONTA and self.SMS_TOKEN and self.SMS_REMETENTE)

    # ── Arquivos enviados ────────────────────────────────────────────
    # Pasta onde fotos e documentos ficam gravados. Relativa à pasta
    # backend/, a não ser que venha um caminho absoluto.
    UPLOADS_DIR: str = "uploads"
    FOTO_MAX_KB: int = Field(default=2048, ge=50, le=10240)
    # Documentos do cadastro do morador (RG, comprovante, escritura).
    DOCUMENTO_MAX_KB: int = Field(default=10240, ge=100, le=20480)
    # Por quanto tempo vale a autorização para enviar esses documentos,
    # contada a partir do cadastro.
    TOKEN_DOCUMENTOS_MIN: int = Field(default=60, ge=5, le=1440)
    # Fotos de visitantes e encomendas são dado pessoal de terceiros
    # (LGPD): passado este prazo, o arquivo é apagado e o registro fica
    # sem foto.
    FOTO_PORTARIA_DIAS: int = Field(default=90, ge=1, le=3650)

    # ── CORS ─────────────────────────────────────────────────────────
    # O front-end é servido de qualquer porta local (o python -m
    # http.server, o Live Server do VS Code, etc.), então a origem é
    # liberada por expressão em vez de uma lista fixa de portas — senão
    # o navegador bloqueia o login com "não foi possível falar com o
    # servidor". Em produção, aponte CORS_ORIGINS para o domínio real.
    CORS_ORIGINS: list[str] = []
    CORS_ORIGIN_REGEX: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    @model_validator(mode="after")
    def _recusar_chave_de_exemplo(self) -> "Settings":
        """Com DEBUG desligado, subir com a chave do .env.example seria
        deixar qualquer um assinar um token: ela está no repositório, e
        é ela que assina o JWT e embaralha os códigos de verificação.
        """
        if not self.DEBUG and self.SECRET_KEY == CHAVE_DE_EXEMPLO:
            raise ValueError(
                "SECRET_KEY ainda é a de exemplo.\n"
                "  Primeira vez aqui? Copie backend/.env.example para "
                "backend/.env — ele já vem com DEBUG=true.\n"
                "  Em produção, gere uma chave própria com:\n"
                "    python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
