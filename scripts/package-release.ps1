param(
    [string]$ExecutablePath = (Join-Path $PSScriptRoot '..\dist\NikkiBook\NikkiBook.exe'),
    [string]$BundlePath = (Join-Path $PSScriptRoot '..\release\NikkiBook-Portable')
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourceSampleData = Join-Path $repoRoot 'sample app pics'
$sourceDatabase = Join-Path $sourceSampleData 'nikkibook.db'
$sourceImages = Join-Path $sourceSampleData 'images'
$sourceThumbs = Join-Path $sourceSampleData 'thumbs'
$sourceClickerAssets = Join-Path $repoRoot 'assets clicker'
$sourceReadme = Join-Path $repoRoot 'packaging\README.txt'
$resolvedExecutable = (Resolve-Path $ExecutablePath).Path
$builtAppDir = Split-Path $resolvedExecutable -Parent
$builtInternalDir = Join-Path $builtAppDir '_internal'
$resolvedBundle = [System.IO.Path]::GetFullPath($BundlePath)
$resolvedReleaseRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'release'))

if (-not $resolvedBundle.StartsWith($resolvedReleaseRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to package outside the repository release directory: $resolvedBundle"
}

foreach ($requiredPath in @($resolvedExecutable, $builtInternalDir, $sourceDatabase, $sourceImages, $sourceThumbs, $sourceClickerAssets, $sourceReadme)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required release input is missing: $requiredPath"
    }
}

if (Test-Path -LiteralPath $resolvedBundle) {
    Remove-Item -LiteralPath $resolvedBundle -Recurse -Force
}

New-Item -ItemType Directory -Path $resolvedBundle -Force | Out-Null
Copy-Item -LiteralPath $resolvedExecutable -Destination (Join-Path $resolvedBundle 'NikkiBook.exe')
Copy-Item -LiteralPath $builtInternalDir -Destination (Join-Path $resolvedBundle '_internal') -Recurse
Copy-Item -LiteralPath $sourceReadme -Destination (Join-Path $resolvedBundle 'Getting started.txt')
Copy-Item -LiteralPath $sourceDatabase -Destination (Join-Path $resolvedBundle 'nikkibook.db')
Copy-Item -LiteralPath $sourceImages -Destination (Join-Path $resolvedBundle 'images') -Recurse
Copy-Item -LiteralPath $sourceThumbs -Destination (Join-Path $resolvedBundle 'thumbs') -Recurse
Copy-Item -LiteralPath $sourceClickerAssets -Destination (Join-Path $resolvedBundle 'assets clicker') -Recurse

$hashLines = Get-ChildItem -LiteralPath $resolvedBundle -File -Recurse |
    Sort-Object FullName |
    ForEach-Object {
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash
        $relative = $_.FullName.Substring($resolvedBundle.Length + 1).Replace('\', '/')
        "$hash  $relative"
    }
Set-Content -LiteralPath (Join-Path $resolvedBundle 'SHA256SUMS.txt') -Value $hashLines -Encoding UTF8

$zipPath = Join-Path (Split-Path $resolvedBundle -Parent) 'NikkiBook-Portable.zip'
$archiveCreated = $false
$maxArchiveAttempts = 6
for ($attempt = 1; $attempt -le $maxArchiveAttempts; $attempt++) {
    try {
        if (Test-Path -LiteralPath $zipPath) {
            Remove-Item -LiteralPath $zipPath -Force -ErrorAction Stop
        }

        Compress-Archive `
            -Path (Join-Path $resolvedBundle '*') `
            -DestinationPath $zipPath `
            -CompressionLevel Optimal `
            -ErrorAction Stop

        $archiveFile = Get-Item -LiteralPath $zipPath -ErrorAction Stop
        if ($archiveFile.Length -le 0) {
            throw "The release archive was created empty."
        }

        $archiveCreated = $true
        break
    }
    catch {
        if ($attempt -eq $maxArchiveAttempts) {
            throw "Could not create the release archive after $maxArchiveAttempts attempts: $($_.Exception.Message)"
        }
        Start-Sleep -Seconds 5
    }
}

if (-not $archiveCreated) {
    throw "Could not create the release archive."
}

Write-Output "Packaged: $resolvedBundle"
Write-Output "Archive: $zipPath"
