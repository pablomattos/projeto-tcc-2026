clc;
clear all;
run H:\path\to\eidors-v3.10\eidors\startup.m

file = dir('Real-Data');

n_1 = n_2 = n_3 = n_4 = 0;

for i=3:52
  n_1 = n_1+1;
  folder_1 = file(i).name;
  frame_1 = importdata(folder_1);
  fram_1 = frame_1;
  fr_1 = fram_1';
  vi_1 = vec(fr_1);
  m_1(:,n_1) = vi_1;
  m_vi1 = m_1';
  v_1 = mean(m_vi1);
  v_i1 = vec(v_1);
endfor

for j=53:102
  n_2 = n_2+1;
  folder_2 = file(j).name;
  frame_2 = importdata(folder_2);
  fram_2 = frame_2;
  fr_2 = fram_2';
  vi_2 = vec(fr_2);
  m_2(:,n_2) = vi_2;
  m_vi2 = m_2';
  v_2 = mean(m_vi2);
  v_i2 = vec(v_2);
endfor

for k=103:152
  n_3 = n_3+1;
  folder_3 = file(k).name;
  frame_3 = importdata(folder_3);
  fram_3 = frame_3;
  fr_3 = fram_3';
  vi_3 = vec(fr_3);
  m_3(:,n_3) = vi_3;
  m_vi3 = m_3';
  v_3 = mean(m_vi3);
  v_i3 = vec(v_3);
endfor

for m=153:202
  n_4 = n_4+1;
  folder_4 = file(m).name;
  frame_4 = importdata(folder_4);
  fram_4 = frame_4;
  fr_4 = fram_4';
  vi_4 = vec(fr_4);
  m_4(:,n_4) = vi_4;
  m_vi4 = m_4';
  v_4 = mean(m_vi4);
  v_i4 = vec(v_4);
endfor

imp = [v_i2,v_i3,v_i4];

vh = v_i1;

for p=1:3
  vi = imp(:,p);
  femm = mk_common_model('e2C', 8);
  %femm.fwd_model.stimulation = mk_stim_patterns(8,1,'{ad}','{ad}',{'no_meas_current'},0.001);
  %femm.fwd_model = rmfield(femm.fwd_model, 'meas_select');
  bkgnd = 20;
  img = mk_image(femm.fwd_model, bkgnd);
  inv_GN                       = eidors_obj('inv_model','GN_solver','fwd_model', img.fwd_model);
  inv_GN.reconst_type          = 'difference';
  inv_GN.solve                 = @inv_solve_diff_GN_one_step;
  inv_GN.RtR_prior             = @prior_noser;
  inv_GN.jacobian_bkgnd.value  = bkgnd;
##   if p==1
##    select_fcn = @(x,y,z)([(x-(0)).^2+(y-(0)).^2+(z-(0)).^2<(0)^2]); 
##    img.elem_data =( 1 + elem_select(femm.fwd_model, select_fcn)*2);  %2;
##    inv_GN.hyperparameter.value  = 0.01;
  if p==1
    select_fcn = @(x,y,z)([(x-(0)).^2+(y-(0)).^2+(z-(0)).^2<(0.157)^2]); 
    img.elem_data =( 1 + elem_select(femm.fwd_model, select_fcn)*2);  %2;
    inv_GN.hyperparameter.value  = 0.01;
  elseif p==2
    select_fcn = @(x,y,z)([(x-(0)).^2+(y-(0)).^2+(z-(0)).^2<(0.198)^2]); 
    img.elem_data =( 1 + elem_select(femm.fwd_model, select_fcn)*2);  %2;
    inv_GN.hyperparameter.value  = 0.01;
  elseif p==3
    select_fcn = @(x,y,z)([(x-(0)).^2+(y-(0)).^2+(z-(0)).^2<(0.215)^2]); 
    img.elem_data =( 1 + elem_select(femm.fwd_model, select_fcn)*2);  %2;
    inv_GN.hyperparameter.value  = 0.01;
  endif
  img1 = inv_solve(inv_GN,vi,vh);
  img1.calc_colours.greylev = -0.15;
  %img.calc_colours.cb_shrink_move = [0.8,0.5,1];
  %img.calc_colours.ref_level = 0.5;
  subplot(1,3,p);
  show_fem(img1,[1,1]); axis off; axis image
endfor
