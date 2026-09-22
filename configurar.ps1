<#
    SmartCondo — instalação e inicialização em um comando só.

    Como rodar (no PowerShell, dentro da pasta do projeto):

        powershell -ExecutionPolicy Bypass -File .\configurar.ps1

    O script confere cada peça na ordem, e quando encontra algo faltando
    diz o que é e resolve — em vez de estourar um traceback de cem linhas.
    Rodar duas vezes não faz mal: ele pula o que já está pronto.
#>

$ErrorActionPreference = "Stop"

$Raiz    = $PSScriptRoot
$Backend = Join-Path $Raiz "backend"
$Front   = Join-Path $Raiz "frontend"

# ── Aparência das mensagens ──────────────────────────────────────────
function Titulo($texto) {
    Write-Host ""
    Write-Host "== $texto" -ForegroundColor Cyan
}
function Ok($texto)     { Write-Host "   [ok] $texto" -ForegroundColor Green }
function Aviso($texto)  { Write-Host "   [!]  $texto" -ForegroundColor Yellow }
function Parar($texto) {
    Write-Host ""
    Write-Host "   [x] $texto" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "  SmartCondo — preparando o ambiente" -ForegroundColor White
Write-Host "  ----------------------------------"

# ── 1. Python ────────────────────────────────────────────────────────
Titulo "Python"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Parar @"
Python não encontrado.
      Instale em https://www.python.org/downloads/ e marque a caixa
      "Add python.exe to PATH" na primeira tela do instalador.
"@
}
$versao = (& python --version 2>&1 | Out-String).Trim()
Ok "$versao"

# ── 2. Dependências ──────────────────────────────────────────────────
Titulo "Dependências do back-end"

Push-Location $Backend
& python -c "import uvicorn, fastapi, alembic, psycopg" 2>$null
if ($LASTEXITCODE -ne 0) {
    Aviso "Faltam bibliotecas. Instalando (pode demorar um minuto)..."
    & python -m pip install --quiet -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Pop-Location; Parar "A instalação das dependências falhou." }
}
Ok "Todas instaladas"

# ── 3. Arquivo .env ──────────────────────────────────────────────────
Titulo "Configuração (.env)"

$env_arquivo = Join-Path $Backend ".env"
if (Test-Path $env_arquivo) {
    Ok "Já existe"
} else {
    Copy-Item (Join-Path $Backend ".env.example") $env_arquivo
    Ok "Criado a partir do .env.example"
}

# ── 4. PostgreSQL instalado? ─────────────────────────────────────────
Titulo "PostgreSQL"

$psql = $null
$noPath = Get-Command psql.exe -ErrorAction SilentlyContinue
if ($noPath) {
    $psql = $noPath.Source
} else {
    foreach ($pasta in @("C:\Program Files\PostgreSQL", "C:\Program Files (x86)\PostgreSQL")) {
        if (Test-Path $pasta) {
            $achado = Get-ChildItem $pasta -Recurse -Filter psql.exe -ErrorAction SilentlyContinue |
                      Sort-Object FullName -Descending | Select-Object -First 1
            if ($achado) { $psql = $achado.FullName; break }
        }
    }
}

if (-not $psql) {
    Pop-Location
    Parar @"
PostgreSQL não encontrado neste computador.
      Baixe em https://www.postgresql.org/download/windows/
      No instalador: anote a senha que você definir para o usuário
      "postgres" e deixe a porta em 5432. Depois rode este script de novo.
"@
}
Ok "psql em $psql"

# ── 5. O serviço está rodando? ───────────────────────────────────────
$servico = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($servico -and $servico.Status -ne "Running") {
    Aviso "O serviço está parado. Iniciando..."
    try {
        Start-Service $servico.Name
        Start-Sleep -Seconds 3
        Ok "Serviço iniciado"
    } catch {
        Pop-Location
        Parar @"
Não consegui iniciar o serviço do PostgreSQL.
      Abra o PowerShell como Administrador e rode este script de novo.
"@
    }
} elseif ($servico) {
    Ok "Serviço rodando ($($servico.Name))"
}

# ── 6. Usuário e banco ───────────────────────────────────────────────
Titulo "Usuário e banco do SmartCondo"

# Talvez já esteja tudo pronto de uma execução anterior. Se estiver, nem
# precisamos pedir a senha do postgres.
$env:PGPASSWORD = "smartcondo"
& $psql -U smartcondo -h 127.0.0.1 -d smartcondo -c "SELECT 1" *> $null
$ja_pronto = ($LASTEXITCODE -eq 0)
Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue

if ($ja_pronto) {
    Ok "Usuário e banco já existem"
} else {
    Write-Host ""
    Write-Host "   Preciso da senha do usuario 'postgres' — aquela que voce" -ForegroundColor White
    Write-Host "   definiu quando instalou o PostgreSQL." -ForegroundColor White
    $segura = Read-Host "   Senha do postgres" -AsSecureString
    $bstr   = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura)
    $env:PGPASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

    & $psql -U postgres -h 127.0.0.1 -d postgres -c "SELECT 1" *> $null
    if ($LASTEXITCODE -ne 0) {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
        Pop-Location
        Parar @"
A senha do usuário "postgres" não foi aceita.
      É a senha que você escolheu durante a instalação do PostgreSQL,
      não a senha do Windows. Se você não lembra, dá para redefinir
      reinstalando o PostgreSQL.
"@
    }
    Ok "Conectado como postgres"

    # O CREATE reclama se já existir; o ALTER logo abaixo acerta a senha
    # de qualquer forma, então o erro do primeiro é esperado e silenciado.
    & $psql -U postgres -h 127.0.0.1 -d postgres -c "CREATE ROLE smartcondo LOGIN PASSWORD 'smartcondo'" *> $null
    & $psql -U postgres -h 127.0.0.1 -d postgres -c "ALTER ROLE smartcondo LOGIN PASSWORD 'smartcondo'" *> $null
    Ok "Usuário smartcondo pronto"

    foreach ($banco in @("smartcondo", "smartcondo_test")) {
        $existe = (& $psql -U postgres -h 127.0.0.1 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$banco'" | Out-String).Trim()
        if ($existe -ne "1") {
            & $psql -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE $banco OWNER smartcondo" *> $null
            Ok "Banco $banco criado"
        } else {
            Ok "Banco $banco já existe"
        }
    }

    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

# ── 7. Tabelas ───────────────────────────────────────────────────────
Titulo "Tabelas"

& python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { Pop-Location; Parar "A criação das tabelas falhou (veja o erro acima)." }
Ok "Tabelas em dia"

# ── 8. Dados de demonstração ─────────────────────────────────────────
Titulo "Contas e dados de demonstração"

& python -m app.seed
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Aviso "O banco já tem dados."
    $resposta = Read-Host "   Apagar tudo e recriar do zero? (s/N)"
    if ($resposta -eq "s" -or $resposta -eq "S") {
        & python -m app.seed --limpar
        if ($LASTEXITCODE -ne 0) { Pop-Location; Parar "Não consegui recriar os dados." }
    } else {
        Ok "Mantendo os dados que já estavam lá"
    }
}

Pop-Location

# ── 9. Front-end ─────────────────────────────────────────────────────
Titulo "Front-end"

Write-Host "   O sistema precisa ser aberto por um servidor — abrir o arquivo"
Write-Host "   direto do disco nao funciona para login."
$abrir = Read-Host "   Abrir o front-end numa janela separada? (S/n)"
if ($abrir -ne "n" -and $abrir -ne "N") {
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$Front'; Write-Host 'Front-end em http://localhost:5500 — feche esta janela para parar.' -ForegroundColor Cyan; python -m http.server 5500"
    )
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:5500/index.html"
    Ok "Front-end em http://localhost:5500"
}

# ── 10. API ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Tudo pronto." -ForegroundColor Green
Write-Host ""
Write-Host "  Contas (todas com a senha smartcondo123):"
Write-Host "    Administrador   admin@smartcondo.com"
Write-Host "    Sindico         sindico@smartcondo.com"
Write-Host "    Porteiro        porteiro@smartcondo.com"
Write-Host "    Morador         morador@smartcondo.com"
Write-Host ""
Write-Host "  Subindo a API. Deixe esta janela aberta; Ctrl+C para parar."
Write-Host ""

Set-Location $Backend
& python -m uvicorn app.main:app --reload
