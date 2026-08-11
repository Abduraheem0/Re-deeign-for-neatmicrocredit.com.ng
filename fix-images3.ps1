$root = Get-Location
$images = Get-ChildItem -Path (Join-Path $root 'images') -File | Select-Object -ExpandProperty Name
$files = Get-ChildItem -Path (Join-Path $root 'html') -Filter *.html -File
$srcHrefPattern = '(?i)(src|href)\s*=\s*(["\'])(?![A-Za-z][A-Za-z0-9+.-]*:|/|\.\.?/|images/)([^"\']+\.(?:png|jpe?g|gif|svg|webp|bmp))\2'
$urlPattern = '(?i)url\(\s*(["\']?)(?![A-Za-z][A-Za-z0-9+.-]*:|/|\.\.?/|images/)([^"\')]+\.(?:png|jpe?g|gif|svg|webp|bmp))\1\s*\)'

Write-Output "Images: $($images.Count)"
Write-Output "Files: $($files.Count)"

foreach ($file in $files) {
    Write-Output "Processing $($file.Name)"
    $text = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $orig = $text

    $text = [regex]::Replace($text, $srcHrefPattern, {
        param($m)
        $path = $m.Groups[3].Value
        $basename = [io.path]::GetFileName($path)
        if ($images -contains $basename) {
            Write-Output "  fixed src/href $path -> ../images/$basename"
            return "$($m.Groups[1].Value)=$($m.Groups[2].Value)../images/$basename$($m.Groups[2].Value)"
        }
        return $m.Value
    })

    $text = [regex]::Replace($text, $urlPattern, {
        param($m)
        $path = $m.Groups[2].Value
        $basename = [io.path]::GetFileName($path)
        if ($images -contains $basename) {
            Write-Output "  fixed url $path -> ../images/$basename"
            $quote = $m.Groups[1].Value
            return "url($quote../images/$basename$quote)"
        }
        return $m.Value
    })

    if ($text -ne $orig) {
        Set-Content -Path $file.FullName -Value $text -Encoding UTF8
        Write-Output "  wrote $($file.Name)"
    }
}
