$root = Get-Location
$images = Get-ChildItem -Path (Join-Path $root 'images') -File | Select-Object -ExpandProperty Name
$files = Get-ChildItem -Path (Join-Path $root 'html') -Filter *.html -File
$srcHrefPattern = '(?i)(?<attr>src|href)\s*=\s*(?<quote>["\'])(?<path>(?![A-Za-z][A-Za-z0-9+.-]*:|/|\.\.?/|images/)([^"\']+\.(?:png|jpe?g|gif|svg|webp|bmp)))\k<quote>'
$urlPattern = '(?i)url\(\s*(?<quote>["\']?)(?<path>(?![A-Za-z][A-Za-z0-9+.-]*:|/|\.\.?/|images/)([^"\')]+\.(?:png|jpe?g|gif|svg|webp|bmp)))\k<quote>\s*\)'

foreach ($file in $files) {
    $text = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $orig = $text

    $text = [regex]::Replace($text, $srcHrefPattern, {
        param($m)
        $path = $m.Groups['path'].Value
        $basename = [io.path]::GetFileName($path)
        if ($images -contains $basename) {
            return "$($m.Groups['attr'].Value)=$($m.Groups['quote'].Value)../images/$basename$($m.Groups['quote'].Value)"
        }
        return $m.Value
    })

    $text = [regex]::Replace($text, $urlPattern, {
        param($m)
        $path = $m.Groups['path'].Value
        $basename = [io.path]::GetFileName($path)
        if ($images -contains $basename) {
            $quote = $m.Groups['quote'].Value
            return "url($quote../images/$basename$quote)"
        }
        return $m.Value
    })

    if ($text -ne $orig) {
        Set-Content -Path $file.FullName -Value $text -Encoding UTF8
        Write-Host "patched $($file.Name)"
    }
}
