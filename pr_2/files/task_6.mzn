% Задача 6: зависимости пакетов из условия.
% Версии (индекс: версия), 0 = пакет не ставим:
%   foo:    1:1.0.0 2:1.1.0
%   left:   1:1.0.0
%   right:  1:1.0.0
%   shared: 1:1.0.0 2:2.0.0
%   target: 1:1.0.0 2:2.0.0
var 0..2: foo;
var 0..1: left;
var 0..1: right;
var 0..2: shared;
var 0..2: target;

% root 1.0.0: foo ^1.0.0 и target ^2.0.0
constraint foo >= 1 /\ foo <= 2;
constraint target = 2;

% foo 1.1.0: left ^1.0.0 и right ^1.0.0
constraint (foo = 2) -> (left = 1 /\ right = 1);
% left 1.0.0: shared >=1.0.0
constraint (left = 1) -> (shared >= 1);
% right 1.0.0: shared <2.0.0
constraint (right = 1) -> (shared = 1);
% shared 1.0.0: target ^1.0.0
constraint (shared = 1) -> (target = 1);

% ставим только то, что реально понадобилось (иначе решатель может
% натащить лишнего: left/right/shared сами по себе ничему не мешают)
constraint (left > 0)   -> (foo = 2);
constraint (right > 0)  -> (foo = 2);
constraint (shared > 0) -> (left > 0 \/ right > 0);

solve satisfy;

array[1..2] of string: fooV    = ["1.0.0","1.1.0"];
array[1..1] of string: leftV   = ["1.0.0"];
array[1..1] of string: rightV  = ["1.0.0"];
array[1..2] of string: sharedV = ["1.0.0","2.0.0"];
array[1..2] of string: targetV = ["1.0.0","2.0.0"];
output [
  "foo "    ++ (if fix(foo) = 0 then "not installed" else fooV[fix(foo)] endif) ++ "\n" ++
  "left "   ++ (if fix(left) = 0 then "not installed" else leftV[fix(left)] endif) ++ "\n" ++
  "right "  ++ (if fix(right) = 0 then "not installed" else rightV[fix(right)] endif) ++ "\n" ++
  "shared " ++ (if fix(shared) = 0 then "not installed" else sharedV[fix(shared)] endif) ++ "\n" ++
  "target " ++ (if fix(target) = 0 then "not installed" else targetV[fix(target)] endif) ++ "\n"
];
