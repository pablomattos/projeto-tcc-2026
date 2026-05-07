function [Fid, NFiles, Mesures]                   = get_data_folder(FolderName)
    ListDATFiles                    = dir(fullfile(FolderName, '*.DAT'));
    NFiles                          = length(ListDATFiles);
    Frames                          = zeros(8,8, NFiles);
    % Open DAT file
    for i = 1:NFiles,
        FileName                    = fullfile(FolderName,ListDATFiles(i).name);
        fprintf('Processing data file %s\\%s...........',FolderName,FileName);    
        % Store frames in a 3D array 
        [Fid, Mesures(:,:,i)]              = get_data_from_dat_file(FileName);
        fclose(Fid);
        fprintf('[Done]\n');        
    end
   end