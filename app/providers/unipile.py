"""UnipileProvider — conexão REAL com o LinkedIn via API do Unipile.

Documentação: https://developer.unipile.com
Base:  https://{DSN}/api/v1
Auth:  header X-API-KEY

Endpoints usados:
  GET  /accounts                      -> listar contas conectadas
  GET  /users/{identifier}            -> perfil (query: account_id)
  POST /linkedin/search               -> busca (query: account_id, limit)
  POST /users/invite                  -> convite de conexão
  GET  /chats                         -> conversas
  GET  /chats/{chat_id}/messages      -> mensagens
  POST /chats/{chat_id}/messages      -> enviar mensagem (multipart)
  POST /chats                         -> iniciar conversa (multipart)
  POST /posts                         -> publicar post (multipart)
"""
from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException

from app.providers.base import ConversaExterna, LinkedInProvider, PerfilLinkedIn

TIMEOUT = 30.0

# O LinkedIn recusa nota de convite acima disso (contas free têm limite menor
# que o Premium; 200 é o valor seguro para todos).
LIMITE_NOTA_CONVITE = 200


class UnipileProvider(LinkedInProvider):
    nome = "unipile"

    def __init__(self, dsn: str, api_key: str, account_id: str = "") -> None:
        if not dsn or not api_key:
            raise HTTPException(
                status_code=503,
                detail="Unipile não configurado: preencha DSN e API Key em Conexões.",
            )
        self.base = f"https://{dsn.strip().rstrip('/')}/api/v1"
        self.api_key = api_key.strip()
        self.account_id = (account_id or "").strip()

    # ------------------------------------------------------------------ HTTP

    def _headers(self, json: bool = True) -> dict[str, str]:
        h = {"X-API-KEY": self.api_key, "accept": "application/json"}
        if json:
            h["content-type"] = "application/json"
        return h

    def _req(
        self,
        metodo: str,
        caminho: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: Any = None,
    ) -> Any:
        url = f"{self.base}{caminho}"
        eh_multipart = data is not None or files is not None

        # O Unipile exige multipart/form-data nesses endpoints. O httpx só
        # monta multipart quando existe `files`; com apenas `data` ele manda
        # x-www-form-urlencoded e a API recusa. Por isso convertemos os campos
        # em partes de multipart (filename None = campo comum de formulário).
        partes: dict[str, Any] | None = None
        if eh_multipart:
            partes = {}
            for chave, valor in (data or {}).items():
                if valor is None:
                    continue
                if isinstance(valor, (list, tuple)):
                    # campos repetidos (ex.: attendees_ids)
                    for i, item in enumerate(valor):
                        partes[f"{chave}[{i}]"] = (None, str(item))
                else:
                    partes[chave] = (None, str(valor))
            for chave, valor in (files or {}).items():
                partes[chave] = valor

        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.request(
                    metodo,
                    url,
                    headers=self._headers(json=not eh_multipart),
                    params=params,
                    json=json,
                    files=partes,  # multipart/form-data (campos + anexos)
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Falha ao falar com o Unipile: {e}")

        if resp.status_code >= 400:
            detalhe = resp.text[:400]
            raise HTTPException(
                status_code=502,
                detail=f"Unipile respondeu {resp.status_code}: {detalhe}",
            )
        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            return {}

    def _exige_conta(self) -> str:
        if not self.account_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Account ID do Unipile não configurado. Em Conexões, cole o ID da "
                    "conta conectada (aparece na página Accounts do painel do Unipile)."
                ),
            )
        return self.account_id

    # ------------------------------------------------------------------ contas

    def listar_contas(self) -> list[dict[str, Any]]:
        dados = self._req("GET", "/accounts")
        return dados.get("items", []) if isinstance(dados, dict) else []

    def testar(self) -> str:
        """Valida credenciais e devolve um resumo das contas conectadas."""
        contas = self.listar_contas()
        if not contas:
            return "Credenciais OK, mas nenhuma conta conectada no Unipile."
        partes = []
        for c in contas[:5]:
            partes.append(f"{c.get('name') or c.get('id')} ({c.get('type', '?')})")
        return "Conectado! Contas: " + ", ".join(partes)

    # ------------------------------------------------------------------ perfil

    def obter_perfil(self, linkedin_url: str) -> PerfilLinkedIn:
        conta = self._exige_conta()
        identificador = _identificador_de_url(linkedin_url)
        if not identificador:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Este lead não tem URL do LinkedIn — não dá para identificar a "
                    "pessoa no provedor. Importe-o pela busca ou preencha a URL."
                ),
            )
        dados = self._req(
            "GET", f"/users/{identificador}", params={"account_id": conta}
        )
        return _para_perfil(dados)

    def obter_perfil_completo(self, linkedin_url: str) -> dict[str, Any]:
        """Perfil cru do LinkedIn — inclui contatos (e-mail, telefone),
        experiências, formação e habilidades."""
        conta = self._exige_conta()
        identificador = _identificador_de_url(linkedin_url)
        if not identificador:
            raise HTTPException(
                status_code=400,
                detail="Este lead não tem URL do LinkedIn.",
            )
        dados = self._req(
            "GET",
            f"/users/{identificador}",
            params={
                "account_id": conta,
                # pede as seções extras do perfil
                "linkedin_sections": "*",
            },
        )
        return dados if isinstance(dados, dict) else {}

    # ------------------------------------------------------------------ busca

    # a busca "classic" devolve no máximo 50 por página
    PAGINA_BUSCA = 50

    def buscar_pessoas(self, termo: str, limite: int = 10) -> list[PerfilLinkedIn]:
        """Busca pessoas paginando até juntar `limite` resultados.

        Sem paginação a API devolve sempre a mesma primeira página.
        """
        conta = self._exige_conta()
        alvo = max(1, limite)

        perfis: list[PerfilLinkedIn] = []
        vistos: set[str] = set()
        cursor = ""

        # trava de segurança para não entrar em laço infinito
        max_paginas = max(1, (alvo // self.PAGINA_BUSCA) + 2)

        for _ in range(max_paginas):
            faltam = alvo - len(perfis)
            if faltam <= 0:
                break

            params: dict[str, Any] = {
                "account_id": conta,
                "limit": min(faltam, self.PAGINA_BUSCA),
            }
            if cursor:
                params["cursor"] = cursor

            dados = self._req(
                "POST",
                "/linkedin/search",
                params=params,
                json={"api": "classic", "category": "people", "keywords": termo},
            )
            if not isinstance(dados, dict):
                break

            itens = dados.get("items", []) or []
            if not itens:
                break

            for i in itens:
                p = _para_perfil(i)
                chave = p.provider_id or p.linkedin_url
                if chave and chave in vistos:
                    continue
                if chave:
                    vistos.add(chave)
                perfis.append(p)
                if len(perfis) >= alvo:
                    break

            cursor = str(dados.get("cursor") or dados.get("paging", {}).get("cursor") or "")
            if not cursor:
                break  # acabaram os resultados

        return perfis

    def buscar_empresas(self, termo: str, limite: int = 10) -> list[dict[str, Any]]:
        conta = self._exige_conta()
        dados = self._req(
            "POST",
            "/linkedin/search",
            params={"account_id": conta, "limit": min(max(limite, 1), 50)},
            json={"api": "classic", "category": "companies", "keywords": termo},
        )
        return dados.get("items", []) if isinstance(dados, dict) else []

    # ------------------------------------------------------------------ ações

    def enviar_convite(
        self, linkedin_url: str, mensagem: str, provider_id: str = ""
    ) -> bool:
        conta = self._exige_conta()

        # a API exige o id INTERNO da pessoa; o public identifier (ana-souza)
        # é recusado com "User ID does not match provider's expected format".
        pid = (provider_id or "").strip()
        if not pid:
            perfil = self.obter_perfil(linkedin_url)
            pid = perfil.provider_id
        if not pid:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Não consegui obter o ID interno dessa pessoa no LinkedIn. "
                    "Refaça a busca para importar o lead com o ID correto."
                ),
            )

        corpo: dict[str, Any] = {"provider_id": pid, "account_id": conta}
        if mensagem:
            corpo["message"] = mensagem[:LIMITE_NOTA_CONVITE]
        self._req("POST", "/users/invite", json=corpo)
        return True

    def seguir(self, linkedin_url: str, provider_id: str = "") -> bool:
        """Segue a pessoa SEM precisar de convite.

        O Unipile não tem um endpoint dedicado de follow, mas expõe
        POST /linkedin (raw), que encaminha chamadas para a API interna do
        LinkedIn. Usamos o endpoint de followingStates.

        ⚠️ API interna: não é documentada e pode mudar sem aviso.
        """
        conta = self._exige_conta()

        pid = (provider_id or "").strip()
        if not pid:
            pid = self.obter_perfil(linkedin_url).provider_id
        if not pid:
            raise HTTPException(
                status_code=400,
                detail="Não consegui identificar a pessoa para seguir.",
            )

        # o urn pode vir completo ou só o id
        urn = pid if pid.startswith("urn:li:") else f"urn:li:fsd_profile:{pid}"
        alvo = f"urn:li:fsd_followingState:urn:li:fsu_profileFollowingState:{urn}"

        self._req(
            "POST",
            "/linkedin",
            json={
                "account_id": conta,
                "method": "POST",
                "request_url": (
                    "https://www.linkedin.com/voyager/api/feed/dash/followingStates/"
                    + alvo
                ),
                "body": {"patch": {"$set": {"following": True}}},
                "headers": {"x-http-method-override": "PATCH"},
            },
        )
        return True

    # ------------------------------------------------------------------ chat

    def listar_conversas(self, limite: int = 50) -> list[ConversaExterna]:
        conta = self._exige_conta()
        dados = self._req(
            "GET", "/chats", params={"account_id": conta, "limit": min(limite, 250)}
        )
        itens = dados.get("items", []) if isinstance(dados, dict) else []
        conversas: list[ConversaExterna] = []
        for c in itens:
            conversas.append(
                ConversaExterna(
                    external_id=str(c.get("id", "")),
                    nome_lead=str(c.get("name") or ""),
                    ultima_mensagem="",
                )
            )
        return conversas

    def listar_mensagens(self, chat_id: str, limite: int = 50) -> list[dict[str, Any]]:
        dados = self._req(
            "GET", f"/chats/{chat_id}/messages", params={"limit": min(limite, 250)}
        )
        return dados.get("items", []) if isinstance(dados, dict) else []

    def enviar_mensagem(self, external_id: str, texto: str) -> bool:
        conta = self._exige_conta()
        # multipart/form-data (conforme a doc)
        self._req(
            "POST",
            f"/chats/{external_id}/messages",
            data={"text": texto, "account_id": conta},
        )
        return True

    def iniciar_conversa(self, provider_id: str, texto: str, inmail: bool = False) -> str:
        """Inicia uma conversa nova. Devolve o chat_id.

        inmail=True usa um crédito de InMail — é o único jeito de mandar
        mensagem no chat para quem NÃO é sua conexão.
        """
        conta = self._exige_conta()
        corpo: dict[str, Any] = {
            "account_id": conta,
            "attendees_ids": provider_id,
            "text": texto,
        }
        if inmail:
            # opções específicas do LinkedIn vão como JSON dentro do multipart
            corpo["linkedin"] = json.dumps({"api": "classic", "inmail": True})
        dados = self._req("POST", "/chats", data=corpo)
        return str(dados.get("chat_id", "")) if isinstance(dados, dict) else ""

    # ------------------------------------------------------- perfil próprio

    def obter_meu_perfil(self) -> dict[str, Any]:
        """Dados do dono da conta conectada (headline, summary, etc.)."""
        conta = self._exige_conta()
        dados = self._req("GET", "/users/me", params={"account_id": conta})
        return dados if isinstance(dados, dict) else {}

    def editar_meu_perfil(self, headline: str = "", summary: str = "") -> bool:
        """Atualiza o próprio perfil do LinkedIn (título e seção 'Sobre')."""
        conta = self._exige_conta()
        corpo: dict[str, Any] = {"type": "LINKEDIN", "account_id": conta}
        if headline:
            corpo["headline"] = headline
        if summary:
            corpo["summary"] = summary
        if len(corpo) == 2:
            raise HTTPException(status_code=400, detail="Nada para atualizar.")
        self._req("PATCH", "/users/me/edit", data=corpo)
        return True

    # ------------------------------------------------------- rede / convites

    def listar_relacoes(self, limite: int = 100, cursor: str = "") -> tuple[list[PerfilLinkedIn], str]:
        """Lista suas conexões. Devolve (perfis, proximo_cursor)."""
        conta = self._exige_conta()
        params: dict[str, Any] = {"account_id": conta, "limit": min(max(limite, 1), 1000)}
        if cursor:
            params["cursor"] = cursor
        dados = self._req("GET", "/users/relations", params=params)
        itens = dados.get("items", []) if isinstance(dados, dict) else []
        proximo = str(dados.get("cursor") or "") if isinstance(dados, dict) else ""

        perfis: list[PerfilLinkedIn] = []
        for r in itens:
            nome = " ".join(
                p for p in [r.get("first_name"), r.get("last_name")] if p
            ).strip()
            publico = str(r.get("public_identifier") or "")
            perfis.append(
                PerfilLinkedIn(
                    nome=nome or publico,
                    headline=str(r.get("headline") or ""),
                    linkedin_url=str(
                        r.get("public_profile_url")
                        or (f"https://www.linkedin.com/in/{publico}" if publico else "")
                    ),
                    provider_id=str(r.get("member_id") or r.get("member_urn") or ""),
                )
            )
        return perfis, proximo

    def listar_convites_enviados(self) -> list[dict[str, Any]]:
        """Convites que ainda estão PENDENTES (quem aceitou some desta lista)."""
        conta = self._exige_conta()
        dados = self._req("GET", "/users/invite/sent", params={"account_id": conta})
        return dados.get("items", []) if isinstance(dados, dict) else []

    def saldo_inmail(self) -> dict[str, Any]:
        conta = self._exige_conta()
        dados = self._req("GET", "/linkedin/inmail_balance", params={"account_id": conta})
        return dados if isinstance(dados, dict) else {}

    # ------------------------------------------------------------------ post

    def publicar_post(self, texto: str, imagem_path: str = "") -> str:
        """Publica no feed. Se houver imagem, vai como anexo (multipart)."""
        conta = self._exige_conta()
        corpo = {"account_id": conta, "text": texto}

        if imagem_path:
            caminho = Path(imagem_path)
            if not caminho.exists():
                raise HTTPException(
                    status_code=400, detail=f"Imagem não encontrada: {imagem_path}"
                )
            conteudo = caminho.read_bytes()
            dados = self._req(
                "POST",
                "/posts",
                data=corpo,
                files={
                    "attachments": (
                        caminho.name,
                        conteudo,
                        _mime_da_imagem(caminho.name),
                    )
                },
            )
        else:
            dados = self._req("POST", "/posts", data=corpo)

        return str(dados.get("post_id", "")) if isinstance(dados, dict) else ""


# ---------------------------------------------------------------- utilidades


def _mime_da_imagem(nome: str) -> str:
    tipo, _ = mimetypes.guess_type(nome)
    return tipo or "application/octet-stream"


def _identificador_de_url(url_ou_id: str) -> str:
    """Extrai o public_identifier de uma URL do LinkedIn.

    'https://linkedin.com/in/ana-souza/' -> 'ana-souza'
    Se já vier um id puro, devolve como está.
    """
    valor = (url_ou_id or "").strip().rstrip("/")
    if "/in/" in valor:
        valor = valor.split("/in/", 1)[1]
        valor = valor.split("/")[0].split("?")[0]
    return valor


_LIXO_NOME = {"undefined", "null", "none", "n/a", ""}


def _parte_nome(valor: Any) -> str:
    """Descarta valores-lixo que o LinkedIn às vezes devolve."""
    texto = str(valor or "").strip()
    return "" if texto.lower() in _LIXO_NOME else texto


def _para_perfil(d: dict[str, Any]) -> PerfilLinkedIn:
    """Converte o JSON do Unipile no nosso PerfilLinkedIn."""
    nome = " ".join(
        p for p in [_parte_nome(d.get("first_name")), _parte_nome(d.get("last_name"))] if p
    ).strip() or _parte_nome(d.get("name"))

    empresa = ""
    cargo = ""
    experiencias = d.get("work_experience") or []
    if isinstance(experiencias, list) and experiencias:
        atual = experiencias[0] or {}
        empresa = str(atual.get("company") or "")
        cargo = str(atual.get("position") or atual.get("title") or "")

    # a busca devolve campos mais enxutos
    if not empresa:
        empresa = str(d.get("current_company") or d.get("company") or "")
    if not cargo:
        cargo = str(d.get("current_position") or "")

    publico = str(d.get("public_identifier") or d.get("public_profile_url") or "")
    if "/in/" in publico:
        publico = publico.rstrip("/").split("/in/", 1)[1].split("/")[0]

    url = (
        d.get("profile_url")
        or d.get("public_profile_url")
        or (f"https://www.linkedin.com/in/{publico}" if publico else "")
    )

    # O id interno vem com nomes diferentes entre perfil e resultado de busca.
    provider_id = str(
        d.get("provider_id")
        or d.get("member_urn")
        or d.get("entity_urn")
        or d.get("id")
        or ""
    )

    return PerfilLinkedIn(
        nome=nome,
        headline=str(d.get("headline") or ""),
        empresa=empresa,
        cargo=cargo,
        linkedin_url=str(url),
        sobre=str(d.get("summary") or d.get("about") or ""),
        posts_recentes=[],
        provider_id=provider_id,
    )
