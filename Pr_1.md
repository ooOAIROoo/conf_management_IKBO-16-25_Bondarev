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

Команда `grep` захватит все что соответствует регулярному выражению `'^[^:]*'` из указанной папки `/passwd`, далее `sort` сортирует

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
