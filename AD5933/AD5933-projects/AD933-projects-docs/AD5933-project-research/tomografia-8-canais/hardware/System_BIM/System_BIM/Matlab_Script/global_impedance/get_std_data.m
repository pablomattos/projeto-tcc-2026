function [Media Standar Y]  = get_std_data(NFiles, X)
Y                           = zeros(1,NFiles);

for i =1:8,
    for j=1:8, 
        for w=1:NFiles,
          % Get in Y vector, the elements ij of each frame
          Y(w)             = X(i,j,w);
          % Get mean and standard deviation of Y
          Media(i,j)       = mean(Y);
          Standar(i,j)     = std(Y);
        end
    end
end