clear all
clc

Case = 4;        % 4-bus, 30-bus, 118-bus
simTime = 2000; % number of iterations

alpha=0.001;     % step size
gamma=0.1;       % barrier shift coefficient
M=0.1;           % barrier curvature (mu)

deltaUpdate=3;   % number of steps in Delta_G (must be integer)

plotres=50;     % resolution of plots

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
PdcState = Nde+1:Nde+Ndc;
PdtState = Nde+Ndc+1:Nde+Ndc+Ndt;
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