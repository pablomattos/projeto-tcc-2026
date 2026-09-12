function [Fid, Data]            = get_data_from_dat_file(FileName)
    Fid                         = fopen(FileName,'rt');
    % Get numerical values 
    Data                        = fscanf(Fid,'%f',[8 8]);    
    Data                        = Data';
end

