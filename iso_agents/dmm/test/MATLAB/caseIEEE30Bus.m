function [baseMVA, bus, gen, branch] = caseIEEE30Bus
% CASE_IEEE30    Power flow data for IEEE 30 bus test case.
%   Please see 'help caseformat' for details on the case file format.
%   This data was converted from IEEE Common Data Format
%   (ieee30cdf.txt) on 20-Sep-2004 by cdf2matp, rev. 1.11
%   See end of file for warnings generated during conversion.
%
%   Converted from IEEE CDF file from:
%       http://www.ee.washington.edu/research/pstca/
% 
%  08/20/93 UW ARCHIVE           100.0  1961 W IEEE 30 Bus Test Case

%   MATPOWER
%   $Id: case_ieee30.m,v 1.3 2007/09/17 16:07:48 ray Exp $

%%-----  Power Flow Data  -----%%
%% system MVA base
baseMVA = 100;
%Off-Peak without smart meter
% bus data
%bus_i	type Pd	Qd	Gs	Bs	area	Vm	Va	baseKV	zone	Vmax	Vmin
bus = [
	1	3	0	0	0	0	1	1.06	 0	    132	1	1.06	0.94;
	2	2	0	0	0	0	1	1.043	-5.48	132	1	1.06	0.94;
	3	1	2.4	0	0	0	1	1.021	-7.96	132	1	1.06	0.94;
	4	1	0	0	0	0	1	1.012	-9.62	132	1	1.06	0.94;
	5	2	0	0	0	0	1	1.01	-14.37	132	1	1.06	0.94;
	6	1	0	0	0	0	1	1.01	-11.34	132	1	1.06	0.94;
	7	1 10.8	0 0	0	1	1.002	-13.12	132	1	1.06	0.94;
	8	1	20	0	0	0	1	1.01	-12.1	132	1	1.06	0.94;
	9	1	15	0	0	0	1	1.051	-14.38	1	1	1.06	0.94;
	10	1	0	0	0	19	1	1.045	-15.97	33	1	1.06	0.94;
	11	2	0	0	0	0	1	1.082	-14.39	11	1	1.06	0.94;
	12	1	0	0	0	0	1	1.057	-15.24	33	1	1.06	0.94;
	13	2	0	0	0	0	1	1.071	-15.24	11	1	1.06	0.94;
	14	1	6.2	0	0	0	1	1.042	-16.13	33	1	1.06	0.94;
	15	1	8.2	0	0	0	1	1.038	-16.22	33	1	1.06	0.94;
	16	1	3.5	0	0	0	1	1.045	-15.83	33	1	1.06	0.94;
	17	1	9	0	0	0	1	1.04	-16.14	33	1	1.06	0.94;
	18	1	0	0	0	0	1	1.028	-16.82	33	1	1.06	0.94;
	19	1	9.5	0	0	0	1	1.026	-17	33	1	1.06	0.94;
	20	1	2.2	0	0	0	1	1.03	-16.8	33	1	1.06	0.94;
	21	1	15.5	0	0	0	1	1.033	-16.42	33	1	1.06	0.94;
	22	1	0	0	0	0	1	1.033	-16.41	33	1	1.06	0.94;
	23	1	3.2	0	0	0	1	1.027	-16.61	33	1	1.06	0.94;
	24	1	8.7	0	0	4.3	1	1.021	-16.78	33	1	1.06	0.94;
	25	1	0	0	0	0	1	1.017	-16.35	33	1	1.06	0.94;
	26	1	3.5	0	0	0	1	1	-16.77	33	1	1.06	0.94;
	27	1	0	0	0	0	1	1.023	-15.82	33	1	1.06	0.94;
	28	1	0	0	0	0	1	1.007	-11.97	132	1	1.06	0.94;
	29	1	2.4	0	0	0	1	1.003	-17.06	33	1	1.06	0.94;
	30	1	10.6	0	0	0	1	0.992	-17.94	33	1	1.06	0.94;
];


%% generator data
%	bus	 Pg 	Qg	 Qmax Qmin	Vg	   mBase	status	Pmax	Pmin
gen = [
	1	260.2 -16.1	 10	   0	1.06	100	    1	100.2	0;
	2	40	  50	 50	  -100	1.045	100  	1	100	    0;
	5	0	  37	 40	  -100	1.01	150 	1	150	    0;
	11	0	 16.2	 24	  -100	1.082	100	    1	150  	0;
	13	0	 10.6	 24	  -40	1.071	100	    1	100	    0;
]; 

%% branch data
%fbus tbus	r	x	    b	rateA	rateB	rateC	ratio	angle	status
branch = [
	1	2	0	0.575	0	100	0	0	0	0	1;
	1	3	0	0.575	0	100	0	0	0	0	1;
	2	4	0	0.575	0	100	0	0	0	0	1;
	3	4	0	0.575	0	100	0	0	0	0	1;
	2	5	0	0.575	0	100	0	0	0	0	1;
	2	6	0	0.575	0	100	0	0	0	0	1;
	4	6	0	0.575	0	100	0	0	0	0	1;
	5	7	0	0.575	0	100	0	0	0	0	1;
	6	7	0	0.575	0	100	0	0	0	0	1;
	6	8	0	0.575	0	100	0	0	0	0	1;
	6	9	0	0.575	0	100	0	0	0	0	1;
	6	10	0	0.575	0	100	0	0	0	0	1;
	9	11	0	0.575	0	100	0	0	0	0	1;
	9	10	0	0.575	0	100	0	0	0	0	1;
	4	12	0	0.575	0	100	0	0	0	0	1;
	12	13	0	0.575	0	100	0	0	0	0	1;
	12	14	0.	0.575	0	100	0	0	0	0	1;
	12	15	0	0.575	0	100	0	0	0	0	1;
	12	16	0	0.575	0	100	0	0	0	0	1;
	14	15	0	0.575	0	100	0	0	0	0	1;
	16	17	0	0.575	0	100	0	0	0	0	1;
	15	18	0	0.575	0	100	0	0	0	0	1;
	18	19	0	0.575	0	100	0	0	0	0	1;
	19	20	0	0.575	0	100	0	0	0	0	1;
	10	20	0	0.575	0	100	0	0	0	0	1;
	10	17	0	0.575	0	100	0	0	0	0	1;
	10	21	0	0.575	0	100	0	0	0	0	1;
	10	22	0	0.575	0	100	0	0	0	0	1;
	21	22	0	0.575	0	100	0	0	0	0	1;
	15	23	0   0.575	0	100	0	0	0	0	1;
	22	24	0	0.575	0	100	0	0	0	0	1;
	23	24	0	0.575	0	100	0	0	0	0	1;
	24	25	0	0.575	0	100	0	0	0	0	1;
	25	26	0	0.575	0	100	0	0	0	0	1;
	25	27	0	0.575	0	100	0	0	0	0	1;
	28	27	0	0.575	0	100	0	0	0	0	1;
	27	29	0	0.575	0	100	0	0	0	0	1;
	27	30	0	0.575	0	100	0	0	0	0	1;
	29	30	0	0.575	0	100	0	0	0	0	1;
	8	28	0	0.575  0	100	0	0	0	0	1;
	6	28	0	0.575	0	100	0	0	0	0	1;
];
% branch = [
% 	1	2	0	0.0575	0.0528	100	0	0	0	0	1;
% 	1	3	0	0.1652	0.0408	100	0	0	0	0	1;
% 	2	4	0	0.1737	0.0368	100	0	0	0	0	1;
% 	3	4	0	0.0379	0.0084	100	0	0	0	0	1;
% 	2	5	0	0.1983	0.0418	100	0	0	0	0	1;
% 	2	6	0	0.1763	0.0374	100	0	0	0	0	1;
% 	4	6	0	0.0414	0.009	100	0	0	0	0	1;
% 	5	7	0	0.116	0.0204	100	0	0	0	0	1;
% 	6	7	0	0.082	0.017	100	0	0	0	0	1;
% 	6	8	0	0.042	0.009	100	0	0	0	0	1;
% 	6	9	0	0.208	0	100	0	0	0.978	0	1;
% 	6	10	0	0.556	0	100	0	0	0.969	0	1;
% 	9	11	0	0.208	0	100	0	0	0	0	1;
% 	9	10	0	0.11	0	100	0	0	0	0	1;
% 	4	12	0	0.256	0	100	0	0	0.932	0	1;
% 	12	13	0	0.14	0	100	0	0	0	0	1;
% 	12	14	0.	0.2559	0	100	0	0	0	0	1;
% 	12	15	0	0.1304	0	100	0	0	0	0	1;
% 	12	16	0	0.1987	0	100	0	0	0	0	1;
% 	14	15	0	0.1997	0	100	0	0	0	0	1;
% 	16	17	0	0.1923	0	100	0	0	0	0	1;
% 	15	18	0	0.2185	0	100	0	0	0	0	1;
% 	18	19	0	0.1292	0	100	0	0	0	0	1;
% 	19	20	0	0.068	0	100	0	0	0	0	1;
% 	10	20	0	0.209	0	100	0	0	0	0	1;
% 	10	17	0	0.0845	0	100	0	0	0	0	1;
% 	10	21	0	0.0749	0	100	0	0	0	0	1;
% 	10	22	0	0.1499	0	100	0	0	0	0	1;
% 	21	22	0	0.0236	0	100	0	0	0	0	1;
% 	15	23	0	0.202	0	100	0	0	0	0	1;
% 	22	24	0	0.179	0	100	0	0	0	0	1;
% 	23	24	0	0.27	0	100	0	0	0	0	1;
% 	24	25	0	0.3292	0	100	0	0	0	0	1;
% 	25	26	0	0.38	0	100	0	0	0	0	1;
% 	25	27	0	0.2087	0	100	0	0	0	0	1;
% 	28	27	0	0.396	0	100	0	0	0.968	0	1;
% 	27	29	0	0.4153	0	100	0	0	0	0	1;
% 	27	30	0	0.6027	0	100	0	0	0	0	1;
% 	29	30	0	0.4533	0	100	0	0	0	0	1;
% 	8	28	0	0.2     0.0428	100	0	0	0	0	1;
% 	6	28	0	0.0599	0.013	100	0	0	0	0	1;
% ];
return;

% Warnings from cdf2matp conversion:
%
% ***** Qmax = Qmin at generator at bus    1 (Qmax set to Qmin + 10)
% ***** area data conversion not yet implemented (creating dummy area data)
% ***** MVA limit of branch 1 - 2 not given, set to 9900
% ***** MVA limit of branch 1 - 3 not given, set to 9900
% ***** MVA limit of branch 2 - 4 not given, set to 9900
% ***** MVA limit of branch 3 - 4 not given, set to 9900
% ***** MVA limit of branch 2 - 5 not given, set to 9900
% ***** MVA limit of branch 2 - 6 not given, set to 9900
% ***** MVA limit of branch 4 - 6 not given, set to 9900
% ***** MVA limit of branch 5 - 7 not given, set to 9900
% ***** MVA limit of branch 6 - 7 not given, set to 9900
% ***** MVA limit of branch 6 - 8 not given, set to 9900
% ***** MVA limit of branch 6 - 9 not given, set to 9900
% ***** MVA limit of branch 6 - 10 not given, set to 9900
% ***** MVA limit of branch 9 - 11 not given, set to 9900
% ***** MVA limit of branch 9 - 10 not given, set to 9900
% ***** MVA limit of branch 4 - 12 not given, set to 9900
% ***** MVA limit of branch 12 - 13 not given, set to 9900
% ***** MVA limit of branch 12 - 14 not given, set to 9900
% ***** MVA limit of branch 12 - 15 not given, set to 9900
% ***** MVA limit of branch 12 - 16 not given, set to 9900
% ***** MVA limit of branch 14 - 15 not given, set to 9900
% ***** MVA limit of branch 16 - 17 not given, set to 9900
% ***** MVA limit of branch 15 - 18 not given, set to 9900
% ***** MVA limit of branch 18 - 19 not given, set to 9900
% ***** MVA limit of branch 19 - 20 not given, set to 9900
% ***** MVA limit of branch 10 - 20 not given, set to 9900
% ***** MVA limit of branch 10 - 17 not given, set to 9900
% ***** MVA limit of branch 10 - 21 not given, set to 9900
% ***** MVA limit of branch 10 - 22 not given, set to 9900
% ***** MVA limit of branch 21 - 22 not given, set to 9900
% ***** MVA limit of branch 15 - 23 not given, set to 9900
% ***** MVA limit of branch 22 - 24 not given, set to 9900
% ***** MVA limit of branch 23 - 24 not given, set to 9900
% ***** MVA limit of branch 24 - 25 not given, set to 9900
% ***** MVA limit of branch 25 - 26 not given, set to 9900
% ***** MVA limit of branch 25 - 27 not given, set to 9900
% ***** MVA limit of branch 28 - 27 not given, set to 9900
% ***** MVA limit of branch 27 - 29 not given, set to 9900
% ***** MVA limit of branch 27 - 30 not given, set to 9900
% ***** MVA limit of branch 29 - 30 not given, set to 9900
% ***** MVA limit of branch 8 - 28 not given, set to 9900
% ***** MVA limit of branch 6 - 28 not given, set to 9900
