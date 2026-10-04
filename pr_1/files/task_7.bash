dir="$1"

for f1 in $(find "$dir" -type f); do
    for f2 in $(find "$dir" -type f); do
        if [[ "$f1" < "$f2" ]] && cmp -s "$f1" "$f2"; then
                echo "Дубликат  $f1 найден"
        fi 
    done
done