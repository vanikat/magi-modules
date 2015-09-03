function [db] = deltabarrier(state,refBus,M,D,B,P,Nt)
%This function gives the gradient of the line capacity barrier functions

%preallocate delta
delta=zeros(length(state)+1);

if refBus==1
    delta=[0 state'];
elseif refBus==length(state)+1
    delta=[state' 0];
else for i=1:refBus-1
        delta(i)=state(i);
    end
    delta(refBus)=0;
    for i=refBus+1:length(state)+1
        delta(i)=state(i-1);
    end
end

%initial gradient set to zero
db(1:length(delta))=0;
db=db';

%add barrier functions
for n=1:Nt
    i=D(n,1);
    j=D(n,2);
    db(i)=db(i)+M*B(i,j)*(1/(B(i,j)*(delta(i)-delta(j))-P(i,j))^2-1/(B(i,j)*(delta(i)-delta(j))+P(i,j))^2);
    db(j)=db(j)+M*B(j,i)*(1/(B(j,i)*(delta(j)-delta(i))-P(j,i))^2-1/(B(j,i)*(delta(j)-delta(i))+P(j,i))^2);
end

%remove reference bus
db(refBus)=[];
end
