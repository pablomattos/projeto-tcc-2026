function [V] = delete_elements_eit_matrix(M)
% Matrix M is transformed into a vector
V                               = M(:);
% The total number of elements to delete
% is 3*NCol
[NRows,NCols]                   = size(M);

% List with the elements of the vector "V"
% to delete
List                            = zeros(3*NCols,1);

% The elements of the first column are deleted
List(1:3)                       = [1;2;NRows];
Pos                             = 4;
% The elements between columns 2 and 7 are deleted
for Col = 1:NCols-2
    List(Pos:Pos+2)             = Col*NRows + (1:3) + (Col-1);
    Pos                         = Pos + 3;
end
% The elements of the last column are deleted
List(Pos:Pos+2)                 = [NRows*(NCols-1)+1; NRows*NCols; NRows*NCols-1];
V(List)                         = [];
end