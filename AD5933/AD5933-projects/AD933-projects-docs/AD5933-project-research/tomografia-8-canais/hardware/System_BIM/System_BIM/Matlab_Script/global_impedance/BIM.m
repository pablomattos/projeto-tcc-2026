function [vh, vi] = TomoAFE4300(Frames, NFiles)
% Load real dates of Tomograph AFE4300

Frames    = Frames./0.001;%(0.07697*Frames)-0.026;%0.05188*Frames;

for i=1:NFiles
    vi(:,:,i) = delete_elements_eit_matrix(Frames(:,:,i)');
end
vh  = vi(:,:,1);

