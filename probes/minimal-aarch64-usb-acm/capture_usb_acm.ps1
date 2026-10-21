[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('(?i)^(?!0000$|ffff$)[0-9a-f]{4}$')]
    [string]$Vid,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('(?i)^(?!0000$|ffff$)[0-9a-f]{4}$')]
    [string]$Pid,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9._-]{1,32}$')]
    [string]$DeviceSerial,

    [ValidateRange(5, 600)]
    [int]$TimeoutSeconds = 120,

    [string]$EvidencePath
)

$ErrorActionPreference = 'Stop'
$marker = 'A02 ARM64 boot probe: PID 1 entered; uname.machine=aarch64'
$startedAt = [DateTimeOffset]::UtcNow
$clock = [System.Diagnostics.Stopwatch]::StartNew()
$received = ''
$outcome = 'INCONCLUSIVE'
$failure = $null
$deviceInstanceId = $null
$friendlyName = $null
$portName = $null
$serial = $null

if ([string]::IsNullOrWhiteSpace($EvidencePath)) {
    $stamp = $startedAt.ToString('yyyyMMddTHHmmssfffZ')
    $EvidencePath = Join-Path (Get-Location) "a02-usb-acm-$stamp.json"
}
$EvidencePath = [System.IO.Path]::GetFullPath($EvidencePath)
if (Test-Path -LiteralPath $EvidencePath) {
    throw "Refusing to overwrite existing evidence file: $EvidencePath"
}
if (!(Test-Path -LiteralPath (Split-Path -Parent $EvidencePath) -PathType Container)) {
    throw 'Evidence directory does not exist; choose an existing local directory.'
}

$vidNorm = $Vid.ToUpperInvariant()
$pidNorm = $Pid.ToUpperInvariant()
$serialPattern = [regex]::Escape($DeviceSerial)
$instancePattern = "(?i)^USB\\VID_$vidNorm&PID_$pidNorm(?:&MI_[0-9A-F]{2})?\\$serialPattern(?:&.*)?$"

function Get-TargetComPort {
    $presentPorts = @(Get-PnpDevice -PresentOnly -Class Ports -ErrorAction Stop)
    $targets = @($presentPorts | Where-Object { $_.InstanceId -match $instancePattern })
    if ($targets.Count -gt 1) {
        return [pscustomobject]@{ State = 'AMBIGUOUS'; Device = $null; Port = $null; Detail = 'More than one present Ports device matches VID/PID/serial.' }
    }
    if ($targets.Count -eq 0) {
        return [pscustomobject]@{ State = 'WAITING'; Device = $null; Port = $null; Detail = $null }
    }

    $device = $targets[0]
    $match = [regex]::Match([string]$device.FriendlyName, '\((COM[0-9]+)\)$', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if (!$match.Success) {
        return [pscustomobject]@{ State = 'WAITING'; Device = $device; Port = $null; Detail = 'Matching USB device is present but has no COM port yet.' }
    }
    return [pscustomobject]@{ State = 'READY'; Device = $device; Port = $match.Groups[1].Value; Detail = $null }
}

try {
    Write-Output "Waiting up to $TimeoutSeconds seconds for USB $vidNorm`:$pidNorm serial $DeviceSerial."
    Write-Output 'Only a COM port attached to that exact present USB PnP identity will be opened.'

    while ($clock.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        $target = Get-TargetComPort
        if ($target.State -eq 'AMBIGUOUS') {
            $outcome = 'AMBIGUOUS'
            $failure = $target.Detail
            break
        }
        if ($null -ne $target.Device) {
            $deviceInstanceId = [string]$target.Device.InstanceId
            $friendlyName = [string]$target.Device.FriendlyName
        }
        if ($target.State -eq 'READY') {
            $portName = $target.Port
            $serial = [System.IO.Ports.SerialPort]::new(
                $portName,
                115200,
                [System.IO.Ports.Parity]::None,
                8,
                [System.IO.Ports.StopBits]::One
            )
            $serial.ReadTimeout = 250
            $serial.DtrEnable = $true
            $serial.RtsEnable = $false
            try {
                $confirmed = Get-TargetComPort
                if ($confirmed.State -eq 'AMBIGUOUS') {
                    $outcome = 'AMBIGUOUS'
                    $failure = $confirmed.Detail
                    break
                }
                if ($confirmed.State -ne 'READY' -or
                    [string]$confirmed.Device.InstanceId -ne $deviceInstanceId -or
                    $confirmed.Port -ne $portName) {
                    continue
                }
                $serial.Open()
                $openedTarget = Get-TargetComPort
                if ($openedTarget.State -ne 'READY' -or
                    [string]$openedTarget.Device.InstanceId -ne $deviceInstanceId -or
                    $openedTarget.Port -ne $portName) {
                    $outcome = 'INCONCLUSIVE'
                    $failure = 'PnP identity changed after opening the port; no capture was attempted.'
                    break
                }
                Write-Output "Opened matched device $friendlyName ($portName); sending no serial payload."
                while ($clock.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
                    $chunk = $serial.ReadExisting()
                    if ($chunk.Length -gt 0) {
                        Write-Output $chunk
                        $received += $chunk
                        if ($received.Length -gt 8192) {
                            $received = $received.Substring($received.Length - 8192)
                        }
                        if ($received.Contains($marker)) {
                            $outcome = 'PASS'
                            break
                        }
                    }
                    Start-Sleep -Milliseconds 100
                }
                if ($outcome -eq 'PASS') { break }
            }
            catch {
                $failure = $_.Exception.Message
                Write-Output 'Matched port is not ready to open; continuing to wait for the same USB identity.'
            }
            finally {
                if ($serial.IsOpen) { $serial.Close() }
                $serial.Dispose()
                $serial = $null
            }
        }
        Start-Sleep -Milliseconds 250
    }
}
catch {
    $failure = $_.Exception.Message
    if ($outcome -ne 'AMBIGUOUS') { $outcome = 'INCONCLUSIVE' }
}
finally {
    if ($null -ne $serial) {
        if ($serial.IsOpen) { $serial.Close() }
        $serial.Dispose()
    }
}

$evidence = [ordered]@{
    schema_version = 1
    capture_started_utc = $startedAt.ToString('o')
    capture_finished_utc = [DateTimeOffset]::UtcNow.ToString('o')
    target = [ordered]@{ vid = $vidNorm; pid = $pidNorm; serial = $DeviceSerial }
    device_instance_id = $deviceInstanceId
    friendly_name = $friendlyName
    com_port = $portName
    expected_marker = $marker
    marker_received = ($outcome -eq 'PASS')
    captured_text_tail = $received
    outcome = $outcome
    detail = $failure
}
$json = ConvertTo-Json -InputObject $evidence -Depth 5
$bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($json)
$stream = [System.IO.File]::Open($EvidencePath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
try { $stream.Write($bytes, 0, $bytes.Length) }
finally { $stream.Dispose() }
Write-Output "Evidence written to $EvidencePath"

if ($outcome -eq 'PASS') {
    Write-Output 'PASS: received the exact AArch64 PID 1 marker.'
    exit 0
}
if ($outcome -eq 'AMBIGUOUS') {
    Write-Output "INCONCLUSIVE: $failure No COM port was opened."
    exit 3
}
Write-Output 'INCONCLUSIVE: target COM device or marker was not observed before timeout; this does not prove boot failure.'
exit 2
