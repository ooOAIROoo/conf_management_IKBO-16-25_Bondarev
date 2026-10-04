# Практика 1
## Задание 1
Выполним команду: 
`grep -o '^[^:]*' /etc/passwd | sort`
```
alpm
avahi
bin
daemon
dbus
flatpak
ftp
git
http
libvirt-qemu
mail
named
nm-openvpn
nobody
...
```

Команда `grep` захватит все что соответствует регулярному выражению `'^[^:]*'` из указанной папки `/passwd`, далее `sort` сортирует.

---

## Задание 2
Выполним команду: `awk '!/^#/ && NF {print $2, $1}' /etc/protocols | sort -rn`
```
255 reserved
147 bit-emu
146 homa
145 nsh
144 aggfrag
143 ethernet
142 rohc
141 wesp
140 shim6
139 hip
138 manet
137 mpls-in-ip
136 udplite
134 rsvp-e2e-ignore
133 fc
132 sctp
131 pipe
130 sps
129 iplt
128 sscopmce
127 crudp
126 crtp
...
```
---

## Задание 3 
Откроем файл `files/task_3.bash` и запишем скрипт.
```bash
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
```

Далее выполним его командой ` bash files/task_3.bash "Hello from RTU MIREA"`.
```
+----------------------+
| Hello from RTU MIREA |
+----------------------+
```
---
## Задание 4 
Запишем в файл `files/task_4` следующее:
`grep -o '[a-zA-Z_][a-zA-Z0-9_]*' "$1" | sort -u | tr '\n' ' '`

Сделаем файл исполнимым `chmod +x task_4.bash`.

Для проверки запишем новый файл `files/test_t4.c`.
```c
int main() {
    int x = 10;
    int y = x + 5;
    return 0;
}
```

И выполним команду `bash files/task_4.bash files/test_t4.c`.
```
int main return x y
```
---
## Задание 5 
Напишем программу для пятого задния: `files/task_5.bash`.
```bash
file_name="$1"
chmod +x "$file_name"
sudo cp "$file_name" /usr/local/bin/
```

Для проверки запишем уже рабочий файл с баннером из папки `files`: `task_3.bash`.
```
sudo ./task_5.bash task_3
```

Далее проверим работу вызвав `task_3.bash` из нового терминала:
```
~/ > task_3.bash "Hi from 3 am"
+--------------+
| Hi from 3 am |
+--------------+
```
---
## Задание 6 
Запишем прошрамму в файл `files/task_6.bash`
```bash
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
```
Создадим пару проверочных файлов:
```
/files> echo "# Python comment" > test.py
/files> echo "int x = 5;" > test.c
```

Вызовем `task_6.bash` и посмотрим на вывод (надо учесть, что в папке `files` лежат и другие файлы с текстом)
```
/files> bash task_6.bash
Файл test.c НЕ содержит комментарий
Файл test_t4.c НЕ содержит комментарий
Файл test.py содержит комментарий

```
---
## Задание 7  
Запишем код задания в файл `files/task_7.bash`
```bash
dir="$1"

for f1 in $(find "$dir" -type f); do
    for f2 in $(find "$dir" -type f); do
        if [[ "$f1" < "$f2" ]] && cmp -s "$f1" "$f2"; then
                echo "Дубликат  $f1 найден"
        fi 
    done
done
```
Создадим тестовые файлы для проверки:
```
echo "aaa" > test_a.txt
echo "aaa" > test_b.txt
```
```
files> bash ./task_7.bash .
Дубликат  ./test_a.txt найден
```
---
## Задание 8  
Запишем скрипт в файл `task_8.bash`
```
dir="$1"
ext="$2"

files=$(find "$dir" -type f -name "*.$ext")

if [ -n "$files" ]; then
    tar -cf archive.tar $files
    echo "Архив archive.tar успешно создан"
else
    echo "Файлы с расширением .$ext не найдены"
fi

```
```
echo "Что то, что можно архивировать и проверить работу 8го задания." > files/test_t8.txt
```
```
> bash files/task_8.bash files txt
архив создан
```

---
## Задание 9  
```
echo "Вот тут >    < 4 пробела" > files/test_t9_in.txt
```

Запишем скрипт `task_9.bash`
```
arg1="$1"
arg2="$2"

sed 's/    /\t/g' "$arg1" > "$arg2"
```

Выполним скрипт:
```
bash files/task_9.bash test_t9_in.txt test_t9_out.txt

```
Теперь посмотрим в файл `test_t9_out.txt` и убедимся что вместо пробелов стоит `\t`

---
## Задание 10 
Создадим скрипт и запишем в файл:
```
dir="$1"

find "$dir" -type f -empty -name "*.txt"
```

Создадим на проверку пустой файл `test_t10_empty.txt` и файл с текстом `test_t10_NOT_empty.txt`
```
touch files/test_t10_empty.txt
echo "не пустой" > files/test_t10_NOT_empty.txt
```

Результат вызова скрипта:
```
> bash files/task_10.bash files
files/test_t10_empty.txt
```