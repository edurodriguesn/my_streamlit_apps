# Vai para a pasta onde está o script
Set-Location $PSScriptRoot

# Nome do ambiente virtual
$VenvPath = "venv"

# Verifica se o venv existe
if (-Not (Test-Path $VenvPath)) {
    Write-Host "Criando ambiente virtual Python..."
    python -m venv $VenvPath

    if (-Not (Test-Path "$VenvPath\Scripts\Activate.ps1")) {
        Write-Error "Falha ao criar o ambiente virtual."
        exit 1
    }
}

# Ativa o venv
Write-Host "Ativando ambiente virtual..."
& "$VenvPath\Scripts\Activate.ps1"

# Mantém o terminal aberto com o venv ativo
Write-Host "Ambiente virtual ativo."
