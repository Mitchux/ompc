
import numpy as _N
import scipy as _S
import pylab as _P

end = None
OMPCSEMI = '_;_'

class OMPCException(Exception):
    pass

class mslice:
    pass


# TODO: make _get_nargout a static method of mfunction
#

def _get_narginout():
    """Return how many values the caller is expecting.
    """
    import inspect, dis
    f = inspect.currentframe()
    # step into the function that called us
    fb = f.f_back
    innames = fb.f_code.co_varnames[:fb.f_code.co_argcount]
    nargin = len([ x for x in innames if fb.f_locals.get(x, None) ])
    # nargout is one frame back
    f = f.f_back.f_back
    c = f.f_code
    i = f.f_lasti
    bytecode = c.co_code
    instruction = ord(bytecode[i+3])
    if instruction == dis.opmap['UNPACK_SEQUENCE']:
        howmany = ord(bytecode[i+4])
        return nargin, howmany
    elif instruction == dis.opmap['POP_TOP']:
        # MATLAB always assumes at least 1 value
        return nargin, 1
    return nargin, 1

class marray:
    pass

class mfunction:
    """Decorator that allows emulation of MATLAB's treatement of functions.
    """
    def __init__(self, retstring):
        self._retvals = tuple( x.strip() for x in retstring.split(",") )
    
    def __call__(self, func):
        from byteplay import Code
        self._func = func
        self._c = Code.from_code(self._func.func_code)
        c = self._c
        
        # all return values must be initialized, for return (retvals)[:nargout]
        # not necessary anymore, the parser has to take care of this
        
        # check for maximum nargout, insert nargin nargout code
        self.__addnarg(c)
        # initialize novel variables, FIXME
        # insert returns, FIXME
    
    def __init_retvals(self, c):
        c.code[:0] = [(LOAD_GLOBAL,),
                      (LOAD_FAST,'args'),
                      (CALL_FUNCTION,1),
                      (STORE_FAST,'nargin'),
                      (LOAD_GLOBAL,'_get_nargout'),
                      (CALL_FUNCTION,0),
                      (STORE_FAST,'nargout')]
    
    def __add_narg(self):
        """Add nargin and nargout variables that emulate their behavior in
        MATLAB.
        """
        self._c.code[:0] = [(LOAD_GLOBAL,'len'),
                      (LOAD_FAST,'args'),
                      (CALL_FUNCTION,1),
                      (STORE_FAST,'nargin'),
                      (LOAD_GLOBAL,'_get_nargout'),
                      (CALL_FUNCTION,0),
                      (STORE_FAST,'nargout')]
        for i, x in enumerate(c.code):
            if x[0] == LOAD_GLOBAL and x[1] == 'nargout':
                c.code[i] = (LOAD_FAST,'nargout')
        func.func_code = c.to_code()
        return func
    
    def __init_novel(self, names):
        """MATLAB allows assignment to variables that are not initialized.
        For example 'a(2) = 1;' would result in 'a = [0 1];'.
        This function takes a list of names as parameters and initializes
        all of them to the default empty marray().
        """
        # find location where the test needs to be made
        # look for (STORE_ATTR, 'lvalue'),
        for instr, name 
        body = []
        for name in names:
            body.extend([(LOAD_GLOBAL,'marray'),
                             (CALL_FUNCTION,0),
                             (STORE_FAST,'')]
        self._c.code[:0] = preamble
        for i, x in enumerate(c.code):
            if x[0] == LOAD_GLOBAL and x[1] == 'nargout':
                self._c.code[i] = (LOAD_FAST,'nargout')
        func.func_code = c.to_code()
        return func
    
    def __add_return(self):
        postfix = []
        for name in self._retvals:                
            postfix += [(LOAD_FAST, name)]
        
        postfix.extend([(BUILD_TUPLE, len(names)),
                        (LOAD_FAST, 'nargout'),
                        (SLICE_2, None),
                        (RETURN_VALUE, None)])
        
        self._c.code.extend(postfix)

@mfunction("out1, out2")
def minmax(x):
    out1 = min(x)
    if nargout > 1:
        out2 = max(x)

def error(msg):
    raise OMPCException(msg)

def _check_nargout(nargout, maxout):
    if nargout > maxout:
        error("Too manu output arguments!")

#@mfunction("out1, out2")
def test_ninout(b=None,c=None):
    out1, out2 = None, None
    nargin, nargout = _get_narginout()
    _check_nargout(nargout, 2)
    print '  nargin = %s, nargout = %d'%(nargin, nargout)
    if nargin == 2:
        out1 = b + c
    elif nargin == 1:
        k = marray()
        out2 = '---'
    k = locals().get('k', marray())
    k(10).lvalue = 12
    return (out1, out2)[:nargout]

a = rand(1,10)
print minmax(a)
mi = minmax(a)
mi, ma = minmax()

a, b, c = test_ninout(3, 4)
a, b = test_ninout(3, 4)

class marrayview:
    def __init__(self, X):
        self._a = X
    def __setitem__(self, i, val):
        print "  Setting [%r] to %r"%(i, val)
        self._a[i] = val
    def __repr__(self):
        return repr(self._a)

class marray(_N.ndarray):
        
    def __init__(self, shp=None, dtype='f8'):
        if shp is None:
            _N.ndarray.__init__(self, 0, dtype, order='FORTRAN')
        else:
            from operator import isSequenceType
            if not isSequenceType(shp):
                shp = [shp, shp]
            elif len(shp) == 1:
                shp.append(shp[0])
            _N.ndarray.__init__(self, shp, dtype, order='FORTRAN')
            self[:] = 0
    
    def __call__(self, *args):
        print 'In', args
        args = [ type(x) is mslice \
                    and slice(x.start-1, x.stop-2, x.step) or x-1 \
                    for x in args ]
        
        return marrayview(self.__getitem__(*args))
        #return self.__getitem__(*args)

def find(cond):
    return _N.where(cond)[0] + 1

def rand(*shape):
    """MATLAB compatible rand.
    """
    from numpy.random import rand, get_state, set_state
    from operator import isSequenceType
    if len(shape) == 0:
        return rand()
    
    if type(shape[0]) is str and shape[0] == 'state':
        if len(shape) == 1:
            return get_state()[2]
        else:
            tp, key, pos = get_state()
            set_state(tp, key, shape[1])
            return
    
    if len(shape) == 1:
        if isSequenceType(shape):
            shape = shape[0]
    
    return rand(*shape)

def size(X, axis1=None):
    """MATLAB compatible size function"""
    nargout = _get_nargout()
    shp = list(_N.shape(X))
    ndim = len(shp)
    if axis1 is None:
        if nargout == 1:
            return shp
        if ndim > nargout:
            shp[nargout-1] = _N.prod(shp[nargout-1:])
            shp = shp[:nargout]
        else:    
            shp += [1]*(nargout-ndim)
    else:
        if axis1 < 1:
            error("Invalid dimension!")
        if axis1 > ndim:
            return 1
        shp = shp[axis1-1]
    return shp

def zeros(*args):
    """MATLAB compatible zeros."""
    from operator import isSequenceType
    args = list(args)
    dtype = 'f8'
    if type(args[-1]) is str:
        dtype = args.pop()
    if len(args) == 1:
        args = args[0]
        if not isSequenceType(args):
            args = [args, args]
    return marray(args, dtype)

def ones(*args):
    """MATLAB compatible ones."""
    return zeros(*args) + 1
