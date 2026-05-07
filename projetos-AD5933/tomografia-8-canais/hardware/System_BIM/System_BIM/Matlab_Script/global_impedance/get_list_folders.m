
function [ListFolders]          = get_list_folders()
    Elements                    = dir();
    ListFolders                 = cell(0,1);
    Count                           = 1;
    for i = 3:length(Elements),
        if Elements(i).isdir == 1,
            ListFolders{Count}  = Elements(i).name;
            Count               = Count + 1;
        end
    end
 end