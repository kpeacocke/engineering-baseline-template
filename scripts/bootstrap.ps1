param(
    [ValidateSet("generic", "python", "ansible")]
    [string]$Profile = "generic",
    [string]$Name,
    [string]$Description,
    [string]$Owner,
    [string]$OwnerName,
    [string]$CodeOwner,
    [string]$AnsibleNamespace,
    [string]$AnsibleCollection,
    [string]$SourceRepository
)

$Arguments = @("scripts/baseline.py", "bootstrap", "--profile", $Profile)
if ($Name) { $Arguments += @("--name", $Name) }
if ($Description) { $Arguments += @("--description", $Description) }
if ($Owner) { $Arguments += @("--owner", $Owner) }
if ($OwnerName) { $Arguments += @("--owner-name", $OwnerName) }
if ($CodeOwner) { $Arguments += @("--codeowner", $CodeOwner) }
if ($AnsibleNamespace) { $Arguments += @("--ansible-namespace", $AnsibleNamespace) }
if ($AnsibleCollection) { $Arguments += @("--ansible-collection", $AnsibleCollection) }
if ($SourceRepository) { $Arguments += @("--source-repository", $SourceRepository) }

python @Arguments
exit $LASTEXITCODE
