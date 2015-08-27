
class DMMUnit(object):
    def __init__(self, params):
        self.rehashParams(params)

    def rehashParams(self,params):
        for key,val in params.iteritems():
            cmd='self.'+key+'='
            if type(val) is str:
                cmd=cmd+'\''+val+'\''
            else:
                cmd=cmd+str(val)
            exec(cmd)