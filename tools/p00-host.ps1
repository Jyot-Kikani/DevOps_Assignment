$ErrorActionPreference = 'Stop'
$machine = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor
$os = Get-CimInstance Win32_OperatingSystem
$disk = Get-PSDrive C
$listeners = @(Get-NetTCPConnection -State Listen | Where-Object LocalPort -in 8080,8081,9090,3000 | Select-Object LocalAddress,LocalPort,OwningProcess)
$browsers = @('C:\Program Files\Google\Chrome\Application\chrome.exe', 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe') | Where-Object {Test-Path -LiteralPath $_} | ForEach-Object { (Get-Item -LiteralPath $_).VersionInfo | Select-Object ProductName,ProductVersion }
[ordered]@{
    memory_bytes = $machine.TotalPhysicalMemory
    logical_cpus = $machine.NumberOfLogicalProcessors
    cpu = $cpu.Name
    os = $os.Caption
    os_version = $os.Version
    disk_free_bytes = $disk.Free
    listeners = $listeners
    browsers = @($browsers)
} | ConvertTo-Json -Depth 5
