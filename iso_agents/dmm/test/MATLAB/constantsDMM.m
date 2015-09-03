function [Nde, Nr, Ndc, Ndt, Ndk, Ng, Nt, Ag, Adc, Adt, Adk, BnmR, BnmSumR, Pmax, PgMax, PgMin, PdcMax, PdcMin, PdtMax, PdtMin, RgMax, RgMin, EdcMax, EdcMin, EdtMax, EdtMinRef, Pdk, cg, cdc, cdt, bg, bdc, bdt, deltag,refBus,D,B,P]=constantsDMM(Case)

[BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN] = idx_bus; 
[GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
[F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, TAP, ...
    SHIFT, BR_STATUS, ANGMIN, ANGMAX] = idx_brch;
[MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;  

%% GenCos Types 
% Type 1
genCo1 = struct('bg'    ,17.2   ... % Base cost
               ,'cg'    ,2.55   ... % Increasing cost 
               ,'deltag',0     ... % Uncertainty in %
               ,'PgMax' ,30     ... % Upper generation bound
               ,'PgMin' ,0      ... % Lower generation bound
               ,'RgMax' ,50     ... % Upper rate bound
               ,'RgMin' ,-50    );  % Lower rate bound
% Type 2
genCo2 = struct('bg'    ,18.8   ... % Base cost
               ,'cg'    ,2.93   ... % Increasing cost 
               ,'deltag',0    ... % Uncertainty in %
               ,'PgMax' ,50    ...  % Upper generation bound
               ,'PgMin' ,0      ... % Lower generation bound
               ,'RgMax' ,100    ... % Upper rate bound
               ,'RgMin' ,-100   );  % Lower rate bound
% Type 3
genCo3 = struct('bg'    ,10     ... % Base cost
               ,'cg'    ,0      ... % Increasing cost
               ,'deltag',20     ... % Uncertainty in %
               ,'PgMax' ,15     ... % Upper generation bound
               ,'PgMin' ,0      ... % Lower generation bound
               ,'RgMax' ,200    ... % Upper rate bound
               ,'RgMin' ,-200   );  % Lower rate bound

%% ConCos Types
% Bucket Type 1
bucketCo1 = struct('bd'    ,60     ... % Base cost
                  ,'cd'    ,-0.41  ... % Increasing cost
                  ,'PdMax' ,100    ... % Upper consumption bound
                  ,'PdMin' ,-100   ... % Lower consumption bound
                  ,'EdMax' ,100    ... % Upper energy bound
                  ,'EdMin' ,-100   );  % Lower energy bound
% Bucket Type 2
bucketCo2 = struct('bd'    ,67     ... % Base cost
                  ,'cd'    ,-0.21  ... % Increasing cost
                  ,'PdMax' ,15     ... % Upper consumption bound
                  ,'PdMin' ,-50    ... % Lower consumption bound
                  ,'EdMax' ,200    ... % Upper energy bound
                  ,'EdMin' ,0      );  % Lower energy bound
% Battery Type 1
batteryCo1 = struct('bd'    ,60     ... % Base cost
                   ,'cd'    ,-0.41  ... % Increasing cost
                   ,'PdMax' ,100    ... % Upper consumption bound
                   ,'PdMin' ,0      ... % Lower consumption bound
                   ,'EdMax' ,200    ... % Upper energy bound
                   ,'Tend'  ,6      );  % End-time
% Battery Type 2
batteryCo2 = struct('bd'    ,67     ... % Base cost
                   ,'cd'    ,-0.21  ... % Increasing cost
                   ,'PdMax' ,50     ... % Upper consumption bound
                   ,'PdMin' ,0      ... % Lower consumption bound
                   ,'EdMax' ,100    ... % Upper energy bound
                   ,'Tend'  ,4      );  % End-time
% Bakery Type 1
bakeryCo1 = struct('Pdk'    ,10     ...  % Power consumption
                  ,'Trun'   ,4      ... % Run-time
                  ,'Tstart' ,1      );  % Start-time
% Bakery Type 2
bakeryCo2 = struct('Pdk'    ,20     ... % Power consumption
                  ,'Trun'   ,4      ... % Run-time
                  ,'Tstart' ,2      );  % Start-time
              
%% Load case             
if Case == 4
    genCoVec=xlsread('DefineCos4','GenCos','B:B');          % Load GenCo types
    conCoDefine = xlsread('DefineCos4','ConCos');           % Load ConCo types
    [baseMVA, bus, gen, branch] = loadcase('caseIEEE4Bus'); % Load case data
elseif Case == 30
    genCoVec=xlsread('DefineCos30','GenCos','B:B');          % Load GenCo types
    conCoDefine = xlsread('DefineCos30','ConCos');           % Load ConCo types
    [baseMVA, bus, gen, branch] = loadcase('caseIEEE30Bus'); % Load case data
elseif Case == 118
    genCoVec=xlsread('DefineCos118v3','GenCos','B:B');          % Load GenCo types
    conCoDefine = xlsread('DefineCos118v3','ConCos');           % Load ConCo types
    [baseMVA, bus, gen, branch] = loadcase('caseIEEE118Bus'); % Load case data
else
    error('Case not defined')
end
 
%% Form vectors with coefficients
bucketVec = conCoDefine(:,2);
batteryVec = conCoDefine(:,3);
bakeryVec = conCoDefine(:,4);

bucketVec(bucketVec==0)=[]; % Remove buses where there is no X consumption
batteryVec(batteryVec==0)=[];
bakeryVec(bakeryVec==0)=[];

%% Numbers
N = size(bus,1);            % Number of buses
Nde = size(bus,1)-1;        % Number of voltage angels
Nr = size(bus,1);           % Number of LMPs
Ndc = length(bucketVec);    % Number of buckets
Ndt = length(batteryVec);   % Number of batteries
Ndk = length(bakeryVec);    % Number of bakeries
Ng = size(gen,1);           % Number of generators
Nt = size(branch,1);        % Number of transmission lines

%% If some of the vectors are empty we need to define these empty vectors
if isempty(bucketVec)
    bucketVecS=[];
    bdc = zeros(1,0);
    cdc = [];
    PdcMax = zeros(1,0);
    PdcMin = zeros(1,0);
    EdcMax = zeros(1,0);
    EdcMin = zeros(1,0);
end
if isempty(batteryVec)
    batteryVecS=[];
    bdt = zeros(1,0);
    cdt = [];
    PdtMax = zeros(1,0);
    PdtMin = zeros(1,0);
    EdtMax = zeros(1,0);
    Tend = zeros(1,0);
    EdtMinRef = zeros(1,0);
end
if isempty(bakeryVec)
    bakeryVecS=[];
    Pdk = zeros(1,0);
    Trun = zeros(1,0);
    Tstart = zeros(1,0);
end

%% Construct vectors with structs
for i=1:Ng  % of GenCo types
    if genCoVec(i) == 1
        genCoVecS(i) = genCo1;
    elseif genCoVec(i) == 2
        genCoVecS(i) = genCo2;
    elseif genCoVec(i) == 3
        genCoVecS(i) = genCo3;
    else
        error('GenCo type not defined')
    end
end
for i=1:Ndc % of bucket types
    if bucketVec(i) == 1
        bucketVecS(i) = bucketCo1;
    elseif bucketVec(i) == 2
        bucketVecS(i) = bucketCo2;
    else
        error('ConCo type not defined')
    end
end
for i=1:Ndt % of battery types
    if batteryVec(i) == 1
        batteryVecS(i) = batteryCo1;
    elseif batteryVec(i) == 2
        batteryVecS(i) = batteryCo2;
    else
        error('ConCo type not defined')
    end
end
for i=1:Ndk % of bakery types
    if bakeryVec(i) == 1
        bakeryVecS(i) = bakeryCo1;
    elseif bakeryVec(i) == 2
        bakeryVecS(i) = bakeryCo2;
    else
        error('ConCo type not defined')
    end
end

%% Coefficient Matrices
for i = 1:Ng
    bg(i) = genCoVecS(i).bg;
    cg(i) = genCoVecS(i).cg;
    deltag(i) = genCoVecS(i).deltag;
    PgMax(i) = genCoVecS(i).PgMax;
    PgMin(i) = genCoVecS(i).PgMin;
    RgMax(i) = genCoVecS(i).RgMax;
    RgMin(i) = genCoVecS(i).RgMin;
end
for i = 1:Ndc
    bdc(i) = bucketVecS(i).bd;
    cdc(i) = bucketVecS(i).cd;
    PdcMax(i) = bucketVecS(i).PdMax;
    PdcMin(i) = bucketVecS(i).PdMin;
    EdcMax(i) = bucketVecS(i).EdMax;
    EdcMin(i) = bucketVecS(i).EdMin;
end
for i = 1:Ndt
    bdt(i) = batteryVecS(i).bd;
    cdt(i) = batteryVecS(i).cd;
    PdtMax(i) = batteryVecS(i).PdMax;
    PdtMin(i) = batteryVecS(i).PdMin;
    EdtMax(i) = batteryVecS(i).EdMax;
    for k = 1:(batteryVecS(i).Tend-1)
        EdtMinRef(i,k) = batteryVecS(i).PdMax*(k-(batteryVecS(i).Tend - 1 - ceil(batteryVecS(i).EdMax/batteryVecS(i).PdMax)))...
            *(batteryVecS(i).PdMax*(k-(batteryVecS(i).Tend - 1 - ceil(batteryVecS(i).EdMax/batteryVecS(i).PdMax)))>0);
    end
end
for i = 1:Ndk
    for k = bakeryVecS(i).Tstart:(bakeryVecS(i).Tstart - 1 + bakeryVecS(i).Trun)
        Pdk(i,k) = bakeryVecS(i).Pdk;
    end
end
bg = bg';
cg = diag(cg);
deltag = diag(deltag);
PgMax = PgMax';
PgMin = PgMin';
RgMax = RgMax';
RgMin = RgMin';
bdc = bdc';
cdc = diag(cdc);
PdcMax = PdcMax';
PdcMin = PdcMin';
EdcMax = EdcMax';
EdcMin = EdcMin';
bdt = bdt';
cdt = diag(cdt);
PdtMax = PdtMax';
PdtMin = PdtMin';
EdtMax = EdtMax';

%% Incident Matrices
% Incident matrix Ag: bus/generator (N x Ng)
Ag = zeros(N,Ng);
genVec = gen(:,GEN_BUS);
for i = 1:Ng
    Ag(genVec(i),i)=1;    
end
% Incident matrix Adc: bus/bucket (N x Ndc)
Adc = zeros(N,Ndc);
conBucket = conCoDefine(:,1:2);
conBucketVec = conBucket(find(conBucket(:,2)>0),1);
for i = 1:Ndc
    Adc(conBucketVec(i),i)=1;    
end
% Incident matrix Adt: bus/battery (N x Ndt)
Adt = zeros(N,Ndt);
conBattery = [conCoDefine(:,1) conCoDefine(:,3)];
conBatteryVec = conBattery(find(conBattery(:,2)>0),1);
for i = 1:Ndt
    Adt(conBatteryVec(i),i)=1;    
end
% Incident matrix Adk: bus/bakery (N x Ndk)
Adk = zeros(N,Ndk);
conBakery = [conCoDefine(:,1) conCoDefine(:,4)];
conBakeryVec = conBakery(find(conBakery(:,2)>0),1);
for i = 1:Ndk
    Adk(conBakeryVec(i),i)=1;    
end

%% Reference bus
refBus=find(bus(:,BUS_TYPE)==3);

%% Transmission line
Ys = 1 ./ branch(:, BR_X);                  % series admittance
f = branch(:, F_BUS);                       % list of "from" buses
t = branch(:, T_BUS);                       % list of "to" buses
Cf = sparse(1:Nt, f, ones(Nt, 1), Nt, N);   % connection matrix for line & from buses
Ct = sparse(1:Nt, t, ones(Nt, 1), Nt, N);   % connection matrix for line & to buses
ii = [1:Nt; 1:Nt]';                         % double set of row indices
Yf = sparse(ii, [f; t], [Ys; -Ys], Nt, N);

BnmSum = Cf' * -Yf + Ct' * Yf ;             % branch admittances
Bnm = -Yf;
BnmSumR = BnmSum;
BnmR = Bnm;
BnmSumR(:,refBus)=[];                       % Delete the column corresponding to the reference bus
BnmR(:,refBus)=[];

BnmSumR=-BnmSumR;                           % sign was wrong
BnmR=-BnmR;                                 % sign was wrong

%Thermal limit of all lines
Pmax=20;
Pmax= Pmax*ones(Nt,1);

%This section constructs matrices D, B, and P for the delta barrier
%function (beta2) calculation

%D is a matrix that gives node connections.  Each row represents a line from
%node (i,1) to (i,2)
%B is a matrix that gives the susceptance of these lines
%P is a matrix that gives the thermal limit of these lines.

D=[f t];
B=zeros(Nt,Nt);
P=zeros(Nt,Nt);

for i=1:Nt
    B(f(i),t(i))=Ys(i);
    B(t(i),f(i))=Ys(i);
    P(f(i),t(i))=Pmax(i);
    P(t(i),f(i))=Pmax(i);
end
end