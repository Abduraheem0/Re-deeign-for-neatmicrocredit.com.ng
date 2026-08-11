var fso = new ActiveXObject('Scripting.FileSystemObject');
var root = fso.GetAbsolutePathName('.');
var imagesFolder = fso.BuildPath(root, 'images');
var htmlFolder = fso.BuildPath(root, 'html');
var htmlFolderObj = fso.GetFolder(htmlFolder);
var imageNames = {};
var imageFiles = new Enumerator(fso.GetFolder(imagesFolder).Files);
for (; !imageFiles.atEnd(); imageFiles.moveNext()) {
    var name = imageFiles.item().Name;
    imageNames[name.toLowerCase()] = true;
}

var srcHrefPattern = /(src|href)\s*=\s*(['"])(?![A-Za-z][A-Za-z0-9+.-]*:|\/|\.\/|\.\.\/|images\/)([^'"\s>]+\.(png|jpe?g|gif|svg|webp|bmp))\2/gi;
var urlPattern = /url\(\s*(['"]?)(?![A-Za-z][A-Za-z0-9+.-]*:|\/|\.\/|\.\.\/|images\/)([^'"\)\s]+\.(png|jpe?g|gif|svg|webp|bmp))\1\s*\)/gi;

function patchFile(file) {
    var text = readAllText(file);
    var original = text;
    text = text.replace(srcHrefPattern, function(match, attr, quote, path) {
        var basename = path.replace(/^.*[\\/]/, '');
        if (imageNames[basename.toLowerCase()]) {
            return attr + '=' + quote + '../images/' + basename + quote;
        }
        return match;
    });
    text = text.replace(urlPattern, function(match, quote, path) {
        var basename = path.replace(/^.*[\\/]/, '');
        if (imageNames[basename.toLowerCase()]) {
            return 'url(' + quote + '../images/' + basename + quote + ')';
        }
        return match;
    });
    if (text !== original) {
        writeAllText(file, text);
        WScript.Echo('patched ' + file.Name);
    }
}

function readAllText(file) {
    var stream = fso.OpenTextFile(file.Path, 1, false, -1);
    var content = stream.ReadAll();
    stream.Close();
    return content;
}

function writeAllText(file, text) {
    var stream = fso.OpenTextFile(file.Path, 2, false, -1);
    stream.Write(text);
    stream.Close();
}

var files = new Enumerator(htmlFolderObj.Files);
for (; !files.atEnd(); files.moveNext()) {
    var file = files.item();
    if (/\.html$/i.test(file.Name)) {
        patchFile(file);
    }
}
