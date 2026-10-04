text="$1"

if [ -z "$text" ]; then
    echo "Ошибка: Укажите текст для вывода."
    echo "Пример: ./banner \"Ваш текст\""
    exit 1
fi

len=${#text}

border="+"
for ((i=0; i<len+2; i++)); do
    border+="-"
done
border+="+"

echo "$border"
echo "| $text |"
echo "$border"
