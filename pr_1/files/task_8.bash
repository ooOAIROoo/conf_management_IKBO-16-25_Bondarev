dir="$1"
ext="$2"

files=$(find "$dir" -type f -name "*.$ext")

if [ -n "$files" ]; then
    tar -cf archive.tar $files
    echo "архив создан"
else
    echo "Файлы с расширением .$ext не найдены"
fi