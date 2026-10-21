param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^COM[0-9]+$')]
    [string]$Port,

    [ValidateRange(5, 600)]
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
$marker = 'A02 ARM64 boot probe: PID 1 entered; uname.machine=aarch64'
$serial = [System.IO.Ports.SerialPort]::new(
    $Port,
    115200,
    [System.IO.Ports.Parity]::None,
    8,
    [System.IO.Ports.StopBits]::One
)
$serial.ReadTimeout = 250
$serial.DtrEnable = $true
$serial.RtsEnable = $false

$clock = [System.Diagnostics.Stopwatch]::StartNew()
$received = ''

try {
    $serial.Open()
    Write-Output "Listening on $Port for the AArch64 PID 1 marker; this script sends no data."

    while ($clock.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        $chunk = $serial.ReadExisting()
        if ($chunk.Length -gt 0) {
            Write-Output $chunk
            $received += $chunk
            if ($received.Length -gt 8192) {
                $received = $received.Substring($received.Length - 8192)
            }
            if ($received.Contains($marker)) {
                Write-Output 'PASS: received the AArch64 PID 1 marker.'
                exit 0
            }
        }
        Start-Sleep -Milliseconds 100
    }

    Write-Output 'INCONCLUSIVE: marker not received before timeout; this does not prove boot failure.'
    exit 2
}
finally {
    if ($serial.IsOpen) {
        $serial.Close()
    }
    $serial.Dispose()
}
