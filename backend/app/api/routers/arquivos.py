"""Entrega das fotos de perfil enviadas pelos usuários."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import arquivos

router = APIRouter(prefix="/arquivos", tags=["Arquivos"])


@router.get("/fotos/{nome}", summary="Foto de perfil", include_in_schema=True)
def foto(nome: str) -> FileResponse:
    caminho = arquivos.caminho_da_foto(nome)
    if caminho is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada.")
    return FileResponse(
        caminho,
        media_type=arquivos.TIPOS[caminho.suffix.lstrip(".")],
        # O nome muda a cada envio, então o conteúdo de um nome nunca
        # muda: o navegador pode guardar à vontade.
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
