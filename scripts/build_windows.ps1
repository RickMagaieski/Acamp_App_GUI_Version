[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptsDirectory = [System.IO.Path]::GetFullPath($PSScriptRoot)
$repositoryRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $scriptsDirectory "..")
)
$expectedScriptsDirectory = [System.IO.Path]::GetFullPath(
    (Join-Path $repositoryRoot "scripts")
)

if ($scriptsDirectory -ne $expectedScriptsDirectory) {
    throw "Não foi possível validar a pasta de scripts do projeto."
}

$entryPoint = Join-Path $repositoryRoot "gui_main.py"
$packageDirectory = Join-Path $repositoryRoot "acamp"
$specification = Join-Path $repositoryRoot "Acamp_App_GUI.spec"
$releaseReadme = Join-Path $repositoryRoot "README_RELEASE.txt"
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

foreach ($requiredPath in @(
    $entryPoint,
    $packageDirectory,
    $specification,
    $releaseReadme,
    $venvPython
)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Arquivo obrigatório ausente: $requiredPath"
    }
}

& $venvPython -c "import PyInstaller"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller não está instalado no ambiente virtual do projeto."
}

Push-Location $repositoryRoot
try {
    if (-not $SkipTests) {
        & $venvPython -m unittest discover -s tests
        if ($LASTEXITCODE -ne 0) {
            throw "Os testes falharam. O empacotamento foi interrompido."
        }
    }

    $buildDirectory = [System.IO.Path]::GetFullPath(
        (Join-Path $repositoryRoot "build")
    )
    $distDirectory = [System.IO.Path]::GetFullPath(
        (Join-Path $repositoryRoot "dist")
    )

    foreach ($generatedDirectory in @($buildDirectory, $distDirectory)) {
        if (
            [System.IO.Path]::GetDirectoryName($generatedDirectory) -ne
            $repositoryRoot
        ) {
            throw "Destino de limpeza inseguro: $generatedDirectory"
        }
        if (Test-Path -LiteralPath $generatedDirectory) {
            Remove-Item -LiteralPath $generatedDirectory -Recurse -Force
        }
    }

    & $venvPython -m PyInstaller `
        --noconfirm `
        --workpath $buildDirectory `
        --distpath $distDirectory `
        $specification
    if ($LASTEXITCODE -ne 0) {
        throw "A compilação do PyInstaller falhou."
    }

    $applicationDirectory = Join-Path $distDirectory "Acamp_App_GUI"
    $executablePath = Join-Path $applicationDirectory "Acamp_App_GUI.exe"
    if (-not (Test-Path -LiteralPath $executablePath -PathType Leaf)) {
        throw "O executável esperado não foi produzido."
    }

    $privateFileNames = @(
        "participants.json",
        "items.json",
        "teams.json",
        "client_secret.json",
        "token.json"
    )
    $bundledPrivateFiles = @(
        Get-ChildItem -LiteralPath $applicationDirectory -Recurse -File |
            Where-Object { $_.Name -in $privateFileNames }
    )
    if ($bundledPrivateFiles.Count -ne 0) {
        throw "A distribuição contém um arquivo privado proibido."
    }

    $userDataDirectory = Join-Path $applicationDirectory "user_data"
    New-Item -ItemType Directory -Path $userDataDirectory -Force |
        Out-Null

    $setupInstructions = @"
Abra Acamp_App_GUI.exe para usar o assistente de configuração.

O assistente permite:
1. Escolher uma pasta existente e usar seus arquivos diretamente.
2. Importar arquivos selecionados com segurança para user_data.

Arquivos obrigatórios:
- participants.json
- items.json
- teams.json

Arquivos Google opcionais:
- client_secret.json
- token.json

Não é necessário copiar arquivos manualmente pelo Explorador de Arquivos.
Não publique arquivos privados nem os adicione ao ZIP. Sem um token
existente, token.json será criado ou atualizado localmente somente após
uma autorização Google iniciada manualmente.
"@
    $setupGuideName = "DATA_SETUP.txt"
    Set-Content `
        -LiteralPath (Join-Path $userDataDirectory $setupGuideName) `
        -Value $setupInstructions `
        -Encoding UTF8

    Copy-Item `
        -LiteralPath $releaseReadme `
        -Destination (Join-Path $applicationDirectory "README_RELEASE.txt")

    $releaseDirectory = [System.IO.Path]::GetFullPath(
        (Join-Path $repositoryRoot "release")
    )
    if (
        [System.IO.Path]::GetDirectoryName($releaseDirectory) -ne
        $repositoryRoot
    ) {
        throw "Destino de release inseguro: $releaseDirectory"
    }
    New-Item -ItemType Directory -Path $releaseDirectory -Force |
        Out-Null
    $archivePath = Join-Path $releaseDirectory "Acamp_App_GUI_Windows.zip"
    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }
    Compress-Archive `
        -LiteralPath $applicationDirectory `
        -DestinationPath $archivePath `
        -CompressionLevel Optimal

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($archivePath)
    try {
        $archiveEntries = @(
            $archive.Entries |
                ForEach-Object { $_.FullName.Replace("\", "/") }
        )
        $archivePrivateFiles = @(
            $archiveEntries |
                Where-Object {
                    [System.IO.Path]::GetFileName($_) -in $privateFileNames
                }
        )
        if ($archivePrivateFiles.Count -ne 0) {
            throw "O arquivo portátil contém um arquivo privado proibido."
        }
        foreach ($requiredEntry in @(
            "Acamp_App_GUI/Acamp_App_GUI.exe",
            "Acamp_App_GUI/README_RELEASE.txt",
            "Acamp_App_GUI/user_data/$setupGuideName"
        )) {
            if ($requiredEntry -notin $archiveEntries) {
                throw "Entrada obrigatória ausente no arquivo portátil."
            }
        }
        $forbiddenArchiveSegments = @(
            "/design_refs/",
            "/tests/",
            "/.git/",
            "/.idea/",
            "/.venv/",
            "/build/",
            "/__pycache__/"
        )
        $forbiddenArchiveEntries = @(
            $archiveEntries |
                Where-Object {
                    $normalized = "/" + $_.TrimStart("/")
                    $hasForbiddenSegment = $false
                    foreach ($segment in $forbiddenArchiveSegments) {
                        if (
                            $normalized.IndexOf(
                                $segment,
                                [System.StringComparison]::OrdinalIgnoreCase
                            ) -ge 0
                        ) {
                            $hasForbiddenSegment = $true
                            break
                        }
                    }
                    $hasForbiddenSegment -or $normalized.EndsWith(
                        ".pyc",
                        [System.StringComparison]::OrdinalIgnoreCase
                    )
                }
        )
        if ($forbiddenArchiveEntries.Count -ne 0) {
            throw "O arquivo portátil contém arquivos de desenvolvimento."
        }
    }
    finally {
        $archive.Dispose()
    }

    Write-Host "Executável criado em: $executablePath"
    Write-Host "Arquivo portátil criado em: $archivePath"
}
finally {
    Pop-Location
}
