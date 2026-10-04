for file in *.c *.js *.py; do
    [ -f "$file" ] || continue
    first_line=$(head -n 1 "$file")

    if [[ "$file" == *.py ]]; then
        if echo "$first_line" | grep -q '^#'; then
            echo "Файл $file содержит комментарий"
        else
            echo "Файл $file НЕ содержит комментарий"
        fi
    fi

    if [[ "$file" == *.c || "$file" == *.js ]]; then
        if echo "$first_line" | grep -qE '^//|^/\*'; then
            echo "Файл $file содержит комментарий"
        else
            echo "Файл $file НЕ содержит комментарий"
        fi
    fi
done
