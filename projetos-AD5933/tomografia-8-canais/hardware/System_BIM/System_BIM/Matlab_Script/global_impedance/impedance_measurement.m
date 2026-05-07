% Example of images reconstrucction with real dates

close all; 
% Parameters model

% Load real data 
ListFolders                = get_list_folders();
[Fid,NFiles, Frames]       = get_data_folder(ListFolders{1});
[vh,vi]                    = TomoAFE4300(Frames, NFiles);

for i=1:NFiles
    
   Imp(i) = sum(sum((vi(:,:,i))./vh)-vh);
     
    
end
plot((Imp))