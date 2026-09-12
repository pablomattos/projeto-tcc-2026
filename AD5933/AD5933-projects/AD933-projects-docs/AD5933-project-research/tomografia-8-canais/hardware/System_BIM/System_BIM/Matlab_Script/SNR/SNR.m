clc;
clear all;


filename = '10ms.txt';
%delimiterIn = '';
%headerlinesIn = 1;
A = importdata(filename);
B = vec2mat(A,65);
B(:,65) = [];
med = mean(B);
media = vec2mat(med,8)
sn = std(B);
Ds = vec2mat(sn,8)
snr = 20*log10(med./sn);
SR = vec2mat(snr,8)
mi = min(snr)
ma = max(snr)
medsnr = mean(snr)
%C = transpose(B);

%for i = 1: 8
  %  for j = 1:8
      
  %   C = snr(i,j)
  %   sn(i) = std(B(:,i));
   % snr = 20*log10(med./sn);
   % end
%end
%stem(snr);


    
