clear all
clc

Case = 30;        % 4-bus, 30-bus, 118-bus
simTime = 10000; % number of iterations

alpha=0.001;     % step size
gamma=0.1;       % barrier shift coefficient
M=0.1;           % barrier curvature (mu)

%deltaUpdate=3;   % number of steps in Delta_G (must be integer)

%Controls how many log entries are present as i mod plotres
plotres=10;     % resolution of plots

c=1; %multiplier constant

k=2; %market clearing interval

%load information about grid layout and market players
   [Nde, Nr, Ndc, Ndt, Ndk, Ng, Nt, Ag, Adc, Adt, Adk, BnmR, ... 
    BnmSumR, Pmax, PgMax, PgMin, PdcMax, PdcMin, PdtMax, PdtMin, RgMax, ...
    RgMin, EdcMax, EdcMin, EdtMax, EdtMinRef, Pdk, cg, cdc, cdt, bg, bdc, ...
    bdt, deltag,refBus,D,B,P]=constantsDMM(Case);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

tic

H11=zeros(Nde,Nde);
H12=zeros(Nde,Ndc);
H13=zeros(Nde,Ndt);
H14=zeros(Nde,Ng);

H21=H12';
H22=eye(Ndc,Ndc);   
%H22=[-cdc];
H23=zeros(Ndc,Ndt);
H24=zeros(Ndc,Ng);

H31=H13';
H32=H23';
H33=eye(Ndt,Ndt);   
%H33=[-cdt];
H34=zeros(Ndt,Ng);

H41=H14';
H42=H24';
H43=H34';
H44=eye(Ng,Ng);     
%H44=cg;

H=[H11 H12 H13 H14
   H21 H22 H23 H24
   H31 H32 H33 H34
   H41 H42 H43 H44];

N=[BnmSumR'
   Adc'
   Adt'
   -Ag'   ];

Hhat=H+c*N*N';
Hhatinv=inv(Hhat);
m1=inv(N'*Hhatinv*N);
m2=N'*Hhatinv;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%define bakery consumption (Pdk) based on types in the case
    if size(Pdk,2) == 0          %zero bakeries
        Adk = zeros(Nde+1,1);
        Pdk = 0;
    else
        Pdk = Pdk(:,k);
    end
    
%set initial state (guess 'one' for generators and consumers)
state = [zeros(Nde,1) ; ones(Ndc,1) ;  ones(Ndt,1);  ones(Ng,1);  zeros(Nr,1) ;  zeros(Nr,1)];

%define state index ranges
deltaState = 1:Nde;

%These are the client entries
%DC is bucket
PdcState = Nde+1:Nde+Ndc;
%DT is battery
PdtState = Nde+Ndc+1:Nde+Ndc+Ndt;
%G is generator
PgState = Nde+Ndc+Ndt+1:Nde+Ndc+Ndt+Ng;

lambdaState = Nde+Ndc+Ndt+Ng+1:Nde+Ndc+Ndt+Ng+Nr;
lambdahatState = Nde+Ndc+Ndt+Ng+Nr+1:Nde+Ndc+Ndt+Ng+Nr+Nr;
PdkState = Nde+Ndc+Ndt+Ng+Nr+Nr+1:Nde+Ndc+Ndt+Ng+Nr+Nr+Ndk;

%plot first point
stateplot(:,1)=[state; Pdk];
time(1)=1;
p=2;

%initialize generation bounds
PgMaxk=zeros(Ng,1);   %this is the barrier location at the current iteration
PgMaxf=zeros(Ng,1);   %this is the final (desired) barrier location

for i = 1:simTime
    %calculate desired generation bounds from renewable generation uncertainties
    for j=1:Ng
       % PgMaxf(j)=PgMax(j)*(1+(deltag(j,j)/100)*(0.5)^(ceil(i/(simTime/deltaUpdate))-1));
       
    end
    
    %calculate the current barrier locations
    for j=1:Ng
    %     PgMaxk(j)=PgMaxk(j)-min((PgMaxk(j)-state(PgState(j)))*gamma,PgMaxk(j)-PgMaxf(j));
    end
    PgMaxk=PgMax;
    
    %calculate gradient of f(x) (without barriers)
    df=[zeros(Nde,1)
        -bdc-cdc*state(PdcState)
        -bdt-cdt*state(PdtState)
        bg+cg*state(PgState)];
    
    %add gradients of barrier functions to gradient of f(x)
    df=df+[deltabarrier(state(deltaState),refBus,M,D,B,P,Nt);
           M./(state(PdcState)-PdcMax).^2-M./(state(PdcState)-(PdcMin)).^2;
           M./(state(PdtState)-PdtMax).^2-M./(state(PdtState)-(PdtMin)).^2;
           M./(state(PgState)-PgMaxk).^2-M./(state(PgState)-(PgMin)).^2];
    
    %calculate h(x)
    h=BnmSumR*state(deltaState)+Adc*state(PdcState)+Adt*state(PdtState)+Adk*Pdk-Ag*state(PgState);
    
    %calculate lambda hat
    state(lambdahatState)=m1*(h-m2*df);
    
    %calculate final gradient of Lagrangian
    G=df+N*state(lambdahatState);

    %x update
    state(1:Nde+Ndc+Ndt+Ng)=state(1:Nde+Ndc+Ndt+Ng)-alpha*Hhatinv*G;
    
    %lambda update
    state(lambdaState)=state(lambdahatState)-alpha*c*h;
    
    %calculate line currents from voltage angles
    current=[BnmR*state(deltaState)];
    
    %display percent complete
    if mod(i,round(simTime/10))==0
       percent_complete=round((i/simTime)*100)
    end
    
    %plot point
    if mod(i,plotres)==0
        stateplot(:,p)=[state;Pdk];
        currentplot(:,p)=current;
        time(p)=p;
        p=p+1;
    end
end
toc
return;

figure(1)
plot(time,stateplot(deltaState,:),'linewidth',1.5)
title('Voltage Angles')
grid on

figure(2)
plot(time,stateplot(lambdaState,:),'linewidth',1.5)
title('Locational Marginal Prices')
grid on

figure(3)
plot(time,stateplot(PdcState,:),'linewidth',1.5)
title('Buckets')
grid on

figure(4)
plot(time,stateplot(PdtState,:),'linewidth',1.5)
title('Batteries')
grid on

figure(5)
plot(time,stateplot(PdkState,:),'linewidth',1.5)
axis([time(1) time(length(time)) 0 25])
title('Bakeries')
grid on

figure(6)
plot(time,stateplot(PgState,:),'linewidth',1.5)
title('Generation')
grid on

figure(7)
plot(time,currentplot,'linewidth',1.5)
title('Line Currents')
grid on



%stateplot contains the log of entire state history, equivalent of what
%goes into mongo DB in python code minus the Pdk entry:
matchingStateLog=stateplot(1:end-1,2:end);
csvwrite('state_log_case_30.csv',matchingStateLog');

%Compare to DETER
stateMATLAB=stateplot(1:end-1,end)';
%This is self.state of the dmm_iso object at the end of the simulation
stateDETER=[2.7070042911893193,-11.432756230836807,-3.148429192727925,6.588425927825038,-1.7937506006390502,1.242349356124542,-4.621104384064019,0.7473496267799106,-4.064814828236659,10.077801504814293,-2.074214230625193,7.330839421494505,-4.793568912054843,-5.909189801678372,-3.8507226681593343,-3.9577687481979957,-6.798239439916168,-7.687289078153953,-6.796895479858594,-6.181395146450177,-6.406428621054049,-8.315342297760612,-8.973075888475309,-10.3557732626573,-12.253271663584032,-9.840972235912515,-5.418609073538527,-11.794753303727113,-11.794753303727113,-2.2919080768317057,4.017395808018891,3.5302175106511324,3.4386316004743875,2.789147419965316,2.8789918278793296,2.90345796899027,3.0947290629688413,3.202979179131327,3.289691857884528,3.040773704420059,3.2029729715267403,3.3000423923489905,3.3979252912844173,3.3979252912844173,26.583029755149788,15.175265937950188,15.968342617344573,16.047868144365545,16.226918004710154,16.356660220510648,55.88552593029155,57.91636045392096,61.16680646311593,59.132053176079694,58.12000377251422,58.52925692052617,58.324923845351655,58.54427286519754,58.58556119619133,58.64263430882567,58.57852284194799,58.918254499789704,58.91075160553661,58.87799431561173,58.83752251341752,58.8265281530687,58.734558644274195,58.7888920046962,58.74035184266682,58.691609903481584,58.65256816888688,58.662234082089384,58.76464494470139,58.69159611867429,58.64763799898468,58.64785753714464,58.6035563196693,58.55898997527257,58.603781636049504,58.60378163604951,55.88552588507299,57.916360408702396,61.166807005738704,59.132053176079694,58.120003727295654,58.52925692052617,58.32492389057022,58.544272910416105,58.58556124140989,58.64263430882567,58.57852279672943,58.918254499789704,58.91075156031805,58.87799436083029,58.83752255863608,58.826528198287264,58.734558644274195,58.7888920046962,58.74035188788538,58.69160994870015,58.65256821410544,58.662234082089384,58.76464498991995,58.691596163892854,58.64763799898468,58.6478575823632,58.6035563196693,58.55898997527257,58.60378168126807,58.603781681268075];
error=sum(abs(stateMATLAB-stateDETER));
if error<1
    disp('Successful Match');
else
    disp('Error Detected');
end


%Investigate a particular unit

%DC-1
%DC-1 State Index:
index=PdcState(1);
%Dispatch over iteration-time
dispatch_dc1=stateplot(index,:);
%index,: is the same as
%{
dispatch_dc1=zeros(1,simTime/plotres);
for i=1:length(dispatch_dc1)
    dispatch_dc1(i)=stateplot(index,i);
end
%}
figure;
plot(dispatch_dc1);




