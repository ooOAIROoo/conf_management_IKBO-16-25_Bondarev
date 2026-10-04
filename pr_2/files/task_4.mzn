% Задача 4: счастливый билет (6 цифр, сумма первых 3 = сумме последних 3),
% все цифры различны (all_different), минимизируем сумму 3 цифр.
array[1..6] of var 0..9: d;                          % цифры билета
constraint sum(i in 1..3)(d[i]) = sum(i in 4..6)(d[i]);  % билет счастливый
constraint all_different(d);                         % все цифры различны
var 0..27: s = sum(i in 1..3)(d[i]);                 % сумма первых трёх цифр
solve minimize s;
output ["ticket: " ++ show(d) ++ "   sum = " ++ show(s)];
