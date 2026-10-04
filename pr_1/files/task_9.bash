arg1="$1"
arg2="$2"

sed 's/    /\t/g' "$arg1" > "$arg2"