param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Arguments
)

$ErrorActionPreference = 'Stop'
python "$PSScriptRoot/scripts/project_factory.py" @Arguments
exit $LASTEXITCODE
