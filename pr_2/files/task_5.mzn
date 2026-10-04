% Задача 5: зависимости пакетов с рисунка из статьи про PubGrub.
% Версии (индекс: версия), 0 = пакет не ставим:
%   menu:     1:1.0.0 2:1.1.0 3:1.2.0 4:1.3.0 5:1.4.0 6:1.5.0
%   dropdown: 1:1.8.0 2:2.0.0 3:2.1.0 4:2.2.0 5:2.3.0
%   icons:    1:1.0.0 2:2.0.0
var 0..6: menu;
var 0..5: dropdown;
var 0..2: icons;

% root 1.0.0 зависит от menu ^1.0.0 и icons ^1.0.0 (<2.0.0)
constraint menu >= 1 /\ menu <= 6;
constraint icons = 1;

% menu >=1.1.0 зависит от dropdown ^2.0.0 ; menu 1.0.0 - от dropdown ^1.0.0
constraint (menu >= 2) -> (dropdown >= 2);
constraint (menu = 1)  -> (dropdown = 1);

% dropdown >=2.0.0 зависит от icons ^2.0.0 ; dropdown 1.8.0 - от icons ^1.0.0
constraint (dropdown >= 2) -> (icons = 2);
constraint (dropdown = 1)  -> (icons = 1);

solve satisfy;

array[1..6] of string: menuV = ["1.0.0","1.1.0","1.2.0","1.3.0","1.4.0","1.5.0"];
array[1..5] of string: dropV = ["1.8.0","2.0.0","2.1.0","2.2.0","2.3.0"];
array[1..2] of string: iconV = ["1.0.0","2.0.0"];
output [
  "menu "     ++ (if fix(menu) = 0 then "not installed" else menuV[fix(menu)] endif) ++ "\n" ++
  "dropdown " ++ (if fix(dropdown) = 0 then "not installed" else dropV[fix(dropdown)] endif) ++ "\n" ++
  "icons "    ++ (if fix(icons) = 0 then "not installed" else iconV[fix(icons)] endif) ++ "\n"
];
