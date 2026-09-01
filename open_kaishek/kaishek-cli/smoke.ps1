$ErrorActionPreference = 'Stop'
$jar = Join-Path $PSScriptRoot 'target/kaishek-cli-0.1.0-SNAPSHOT.jar'
if (!(Test-Path -LiteralPath $jar)) { throw "Build first: mvn package" }
$profile = (& java -jar $jar profile | ConvertFrom-Json)
if ($profile.status -ne 'OK') { throw 'profile smoke failed' }
$parse = ('foo = { bar = 1 }' | & java -jar $jar parse | ConvertFrom-Json)
if ($parse.status -ne 'PARSED' -or !$parse.roundTrip) { throw 'parse smoke failed' }
$unknown = (& java -jar $jar profile --id future | ConvertFrom-Json)
if ($unknown.status -ne 'UNSUPPORTED') { throw 'unsupported smoke failed' }
Write-Output 'kaishek-cli smoke: PASS'
